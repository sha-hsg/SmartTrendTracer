import re
import json
import logging
from pathlib import Path
from typing import Dict, Optional

from bs4 import BeautifulSoup

from app.services.forwarded_email_cleaner import ForwardedEmailCleaner
from app.services.aggressive_html_cleaner import AggressiveHTMLCleaner
from app.collectors.substack_content_cleaners import (
    remove_substack_footer,
    clean_markdown,
    validate_and_fix_content,
)

logger = logging.getLogger(__name__)

# Re-export so existing imports like
#   from app.collectors.substack_parser import remove_substack_footer
# continue to work.
__all__ = ['SubstackParser', 'remove_substack_footer']


class SubstackParser:

    def __init__(self):
        self.markdown_options = {
            'heading_style': 'ATX',  # Use # for headings
            'bullets': '-',  # Use - for bullets
            'strong_em_symbol': '**',  # Use ** for bold
            'wrap': False,  # Don't wrap lines
            'strip': ['script', 'style', 'meta', 'noscript']  # Remove these tags
        }

    def extract_html_body(self, payload) -> str:
        """Extract HTML body from email payload"""
        html_body = ""

        # Check if it's multipart
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/html':
                    import base64
                    data = part['body']['data']
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
                elif 'parts' in part:
                    # Nested multipart
                    html_body = self.extract_html_body(part)
                    if html_body:
                        break
        else:
            # Single part message
            if payload['body'].get('data'):
                import base64
                html_body = base64.urlsafe_b64decode(
                    payload['body']['data']).decode('utf-8', errors='ignore')

        return html_body

    def parse_author_from_sender(self, sender: str, email_body: str = None) -> Dict:
        """Parse author information from sender field or forwarded email"""

        # Load forwarded authors config if available
        config_path = Path(__file__).parent.parent.parent / 'forwarded_authors.json'
        forwarded_authors = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                forwarded_authors = {
                    author['email'].lower(): author
                    for author in config.get('forwarded_authors', [])
                }

        # Check if this is a forwarded email by looking for configured authors in the content
        if email_body and forwarded_authors:
            # Convert HTML to text for cleaner searching
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(email_body, 'html.parser')
            text_content = soup.get_text()

            # Look for each configured author in the email content
            for email, author_config in forwarded_authors.items():
                # Check multiple patterns that might indicate this author
                author_indicators = [
                    author_config['name'],                    # "Nathan Lambert"
                    author_config.get('newsletter', ''),     # "Interconnects"
                    email,                                    # "robotic@substack.com"
                    email.split('@')[0]                       # "robotic"
                ]

                # If any of these indicators appear in the email, attribute to this author
                for indicator in author_indicators:
                    if indicator and indicator.lower() in text_content.lower():
                        username = email.split('@')[0]
                        return {
                            'name': author_config['name'],
                            'subdomain': username,
                            'email': email
                        }

        # Handle self-forwarded emails (from:me to:me) by checking subject and content
        if 'siegfried.handschuh@gmail.com' in sender or 'from:me to:me' in str(email_body):
            # This is a self-forwarded email, try to identify the author from content
            if email_body and forwarded_authors:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(email_body, 'html.parser')
                text_content = soup.get_text()

                # Look for configured authors in content
                for email, author_config in forwarded_authors.items():
                    author_indicators = [
                        author_config['name'],
                        author_config.get('newsletter', ''),
                        email.split('@')[0]
                    ]

                    for indicator in author_indicators:
                        if indicator and indicator.lower() in text_content.lower():
                            username = email.split('@')[0]
                            return {
                                'name': author_config['name'],
                                'subdomain': username,
                                'email': email
                            }

            # If we can't identify a configured author, return a generic forwarded entry
            return {
                'name': 'Siegfried Handschuh',
                'subdomain': 'siegfried.handschuh',
                'email': 'siegfried.handschuh@unisg.ch'
            }

        # Handle direct Substack emails
        match = re.match(r'([^<]+)\s*<([^@]+)@([^>]+)>', sender)
        if match:
            name = match.group(1).strip()
            username = match.group(2).strip()
            domain = match.group(3).strip()

            # Check if this is a configured author (direct subscription)
            email_address = f"{username}@{domain}".lower()
            if email_address in forwarded_authors:
                author_config = forwarded_authors[email_address]
                return {
                    'name': author_config['name'],
                    'subdomain': username,
                    'email': author_config['email']
                }

            # Extract subdomain for other Substack emails
            if 'substack.com' in domain:
                subdomain = username
            else:
                subdomain = username

            return {
                'name': name,
                'subdomain': subdomain,
                'email': f"{username}@{domain}"
            }

        # Fallback
        return {'name': sender, 'subdomain': 'unknown', 'email': sender}

    def clean_forwarded_content(self, html_body: str) -> str:
        """Remove forwarded email headers and artifacts from HTML"""
        if not html_body:
            return html_body

        # For forwarded emails, we don't want to clean too aggressively
        # since the content is embedded within the forwarded structure
        # Instead, just return the original HTML and let the parser handle it

        # Only do minimal cleaning - remove tracking pixels and obvious forward artifacts
        soup = BeautifulSoup(html_body, 'html.parser')

        # Remove tracking pixels (1x1 images)
        for img in soup.find_all('img'):
            try:
                width = img.get('width')
                height = img.get('height')
                src = img.get('src', '')

                # Remove 1x1 tracking pixels
                if ((width == '1' and height == '1') or
                    'open?token=' in src or
                    '/track' in src):
                    img.decompose()
            except (AttributeError, TypeError):
                pass

        # Only remove very specific forwarding header elements, not entire containers
        # Remove only the small divs that are purely forwarding metadata
        divs_to_remove = []
        for div in soup.find_all('div', class_='ms-outlook-mobile-reference-message'):
            div_text = div.get_text(strip=True)
            # Only remove if it's JUST forwarding headers (short text with no content paragraphs)
            if ('From:' in div_text and 'Date:' in div_text and 'Subject:' in div_text and
                len(div_text) < 300 and
                not div.find_all(['p'], class_=lambda x: x and ('body' in x or 'markup' in x))):
                divs_to_remove.append(div)

        for div in divs_to_remove:
            div.decompose()

        return str(soup)

    def clean_markdown(self, markdown: str) -> str:
        """Clean up converted markdown and remove table artifacts.

        Delegates to the standalone helper in substack_content_cleaners.
        """
        return clean_markdown(markdown)

    def validate_and_fix_content(self, markdown: str, is_forwarded: bool, check_only: bool = False) -> str:
        """Validate that we have actual article content and fix if needed.

        Delegates to the standalone helper in substack_content_cleaners.
        """
        return validate_and_fix_content(markdown, is_forwarded, check_only)

    def parse_substack_html(self, html_body: str, check_only: bool = False) -> Dict:
        """Parse Substack-specific content from HTML

        Args:
            html_body: The HTML content to parse
            check_only: If True, suppress warnings (used when checking existing articles)
        """
        if not html_body:
            return {}

        # Initialize cleaners (not using DocumentConverter for emails)
        email_cleaner = ForwardedEmailCleaner()
        aggressive_cleaner = AggressiveHTMLCleaner()

        # Check if this is a forwarded email
        is_forwarded = (
            'ms-outlook-mobile-reference-message' in html_body or
            ('From:' in html_body and 'Date:' in html_body and '@substack.com' in html_body) or
            'Original Message' in html_body or
            'Forwarded message' in html_body
        )

        if is_forwarded:
            print("  📧 Detected forwarded email, applying aggressive cleaning...")
            # For forwarded emails, skip the email cleaner if it would remove all content
            # First check what the cleaner would do
            test_cleaned = email_cleaner.clean_html(html_body)

            # If the cleaner removes too much content, use original HTML
            if len(test_cleaned) < 200 and len(html_body) > 10000:
                print("  ⚠️  Email cleaner too aggressive, using original HTML")
                # Use original HTML for aggressive cleaner
                clean_content = aggressive_cleaner.extract_clean_text(html_body)
            else:
                # Use cleaned HTML
                html_body = test_cleaned
                clean_content = aggressive_cleaner.extract_clean_text(html_body)

            # Extract title from the clean content (usually first heading)
            title = None
            if clean_content:
                lines = clean_content.split('\n')
                for line in lines[:5]:  # Check first 5 lines
                    if line.startswith('# '):
                        title = line[2:].strip()
                        break

            # Since clean_content is already in markdown format with images,
            # we'll skip the normal HTML processing and go straight to markdown
            if clean_content:
                # Skip all the HTML processing and use the cleaned content directly
                markdown = clean_content

                # Clean up the markdown
                markdown = self.clean_markdown(markdown)

                # Remove Substack footer content
                markdown = remove_substack_footer(markdown)

                # Validate content quality and clean invisible characters
                markdown = self.validate_and_fix_content(markdown, is_forwarded, check_only)

                # Extract preview AFTER cleaning
                preview = markdown[:500].strip() + '...' if len(markdown) > 500 else markdown

                # Count words from cleaned markdown
                word_count = len(markdown.split())
                reading_time = max(1, word_count // 200)

                # Try to extract URL from original HTML
                original_soup = BeautifulSoup(html_body, 'html.parser')
                url = None
                for link in original_soup.find_all('a', href=True):
                    if 'substack.com/p/' in link['href']:
                        url = link['href']
                        break

                return {
                    'title': title or 'Use Email Subject',
                    'subtitle': None,
                    'url': url,
                    'content_html': html_body,  # Keep original for reference
                    'content_markdown': markdown,
                    'preview': preview,
                    'word_count': word_count,
                    'reading_time_minutes': reading_time
                }

        # Parse the cleaned HTML
        soup = BeautifulSoup(html_body, 'html.parser')

        # Regular Substack processing (for both direct subscriptions and cleaned forwarded emails)
        # Extract article title - look for h1, h2, or the first substantial heading
        title = None
        if not is_forwarded:  # Only extract title from content for non-forwarded emails
            for tag in ['h1', 'h2']:
                title_tags = soup.find_all(tag)
                for title_tag in title_tags:
                    text = title_tag.get_text(strip=True)
                    # Skip empty or very short titles
                    if text and len(text) > 3 and not any(x in text for x in ['From:', 'Date:', 'Subject:']):
                        title = text
                        break
                if title:
                    break

        # Extract subtitle if present
        subtitle = None
        subtitle_tag = soup.find('p', class_='subtitle') or \
                      soup.find('div', class_='subtitle')
        if subtitle_tag:
            subtitle = subtitle_tag.get_text(strip=True)

        # Convert to markdown - extract content directly from soup
        # Remove scripts and styles first
        for tag in soup(['script', 'style']):
            tag.decompose()

        # First, handle Substack's image tables (they wrap images in table.image-wrapper)
        for table in soup.find_all('table', class_='image-wrapper'):
            img = table.find('img')
            if img:
                src = img.get('src', '')
                alt = img.get('alt', '') or 'Image'

                # Only keep content images
                if 'substack-post-media' in src:
                    # Create markdown image to replace the entire table structure
                    img_markdown = f"\n\n![{alt}]({src})\n\n"
                    table.replace_with(img_markdown)
                else:
                    table.decompose()

        # Then process remaining standalone images
        for img in soup.find_all('img'):
            try:
                src = img.get('src', '') if img.get('src') else ''
                alt = img.get('alt', '') if img.get('alt') else ''
                width = img.get('width', '')
                height = img.get('height', '')

                # Remove tracking pixels and tiny images
                if ('open?token=' in src or  # Tracking pixels
                    '/track' in src or
                    'pixel' in src.lower() or
                    src.startswith('data:image/gif;base64,R0lGOD')):  # 1x1 transparent gifs
                    img.decompose()
                    continue

                # Skip very small images (likely icons) UNLESS they're from post media
                if width and height:
                    try:
                        w = float(width)
                        h = float(height)
                        if w <= 40 and h <= 40 and 'substack-post-media' not in src:
                            img.decompose()
                            continue
                    except (ValueError, TypeError):
                        pass

                # Keep content images from Substack CDN
                if ('substackcdn.com/image/fetch' in src and
                    'substack-post-media' in src):  # This is a real content image
                    # Clean up the URL if needed (remove size parameters for cleaner markdown)
                    # Extract the actual image URL from the CDN wrapper
                    if 'https%3A%2F%2Fsubstack-post-media' in src:
                        # It's URL encoded, keep as is
                        clean_src = src
                    else:
                        clean_src = src

                    # Use alt text if available, otherwise use a generic description
                    img_alt = alt if alt else "Image"

                    # Create markdown image
                    img_markdown = f"\n\n![{img_alt}]({clean_src})\n\n"

                    # Replace the img tag with markdown
                    img.replace_with(img_markdown)
                elif alt and len(alt) > 10:  # Images with meaningful alt text
                    # Keep these as well
                    img_markdown = f"\n\n![{alt}]({src})\n\n"
                    img.replace_with(img_markdown)
                else:
                    # Remove other images (buttons, icons, profile pics, etc)
                    img.decompose()
            except Exception as e:
                # If we can't process an image, remove it
                try:
                    img.decompose()
                except (AttributeError, TypeError):
                    pass

        # Extract all content including text and markdown images
        text_parts = []

        # Use the DocumentConverter for better HTML to Markdown conversion
        # First, clean up the HTML content to keep only article body
        # Remove forwarding headers and metadata
        for tag in soup.find_all(['div', 'span']):
            text = tag.get_text(strip=True)
            if any(marker in text[:100] for marker in ['From:', 'Date:', 'To:', 'Subject:', 'View in browser']):
                tag.decompose()

        # Convert the cleaned HTML to markdown
        # For emails, we DON'T want to use browser-based conversion
        # Use direct HTML processing instead
        try:
            # Get the HTML content after cleanup
            cleaned_html = str(soup)

            # For emails, use html2text directly (not browser-based conversion)
            import html2text
            h = html2text.HTML2Text()
            h.body_width = 0  # Don't wrap
            h.ignore_links = False
            h.ignore_images = False  # Keep images
            h.ignore_tables = False  # Keep tables for layout
            h.images_to_alt = False  # Keep as markdown images
            h.unicode_snob = True
            h.wrap_links = False
            h.skip_internal_links = False

            markdown = h.handle(cleaned_html)

            # Additional cleanup for forwarded emails using the cleaner
            if is_forwarded and markdown:
                markdown = email_cleaner.clean_markdown(markdown)
        except Exception as e:
            logger.warning(f"Error converting HTML to markdown: {e}")
            # Fallback to basic extraction
            markdown = soup.get_text(separator='\n', strip=True)

        # If extraction still failed, try basic text extraction
        if not markdown or len(markdown) < 100:
            # Try to get at least something from the body
            body_text = soup.get_text(separator='\n', strip=True)
            # Remove forwarding headers
            lines = body_text.split('\n')
            clean_lines = []
            skip_until_content = True
            for line in lines:
                if skip_until_content:
                    # Skip forwarding metadata
                    if any(x in line for x in ['From:', 'Date:', 'Subject:', 'To:']):
                        continue
                    # Found actual content
                    if line and len(line) > 20 and not line.startswith('View'):
                        skip_until_content = False
                if not skip_until_content:
                    clean_lines.append(line)
            markdown = '\n\n'.join(clean_lines)

        # Clean up markdown
        markdown = self.clean_markdown(markdown)

        # Remove Substack footer content (copyright, promotional buttons, etc.)
        markdown = remove_substack_footer(markdown)

        # Validate content quality and clean invisible characters
        markdown = self.validate_and_fix_content(markdown, is_forwarded, check_only)

        # Extract preview AFTER cleaning (first 500 chars)
        preview = markdown[:500].strip() + '...' if len(markdown) > 500 else markdown

        # Count words from cleaned markdown
        word_count = len(markdown.split())
        reading_time = max(1, word_count // 200)  # Assume 200 words per minute

        # Try to extract the article URL
        url = None
        view_online_link = soup.find('a', string=re.compile('View online', re.I))
        if view_online_link:
            url = view_online_link.get('href')
        else:
            # Look for any substack.com link
            for link in soup.find_all('a', href=True):
                if 'substack.com/p/' in link['href']:
                    url = link['href']
                    break

        return {
            'title': title or ('Use Email Subject' if is_forwarded else 'Untitled'),
            'subtitle': subtitle,
            'url': url,
            'content_html': html_body,
            'content_markdown': markdown,
            'preview': preview,
            'word_count': word_count,
            'reading_time_minutes': reading_time
        }
