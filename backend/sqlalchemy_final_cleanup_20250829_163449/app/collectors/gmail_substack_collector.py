"""
Gmail-based Substack Newsletter Collector
Fetches Substack newsletters from Gmail and converts them to Markdown
"""
import os
import re
import base64
import pickle
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle, SubstackCollection
from app.services.forwarded_email_cleaner import ForwardedEmailCleaner
from app.services.aggressive_html_cleaner import AggressiveHTMLCleaner

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def remove_substack_footer(content: str) -> str:
    """
    Remove Substack footer content including copyright and promotional buttons
    
    Patterns to remove:
    - Copyright notice (© 2025 Author/Company)
    - Address information
    - Unsubscribe/disable email links
    - "Start writing" promotional buttons
    - "Get the app" promotional buttons
    - Associated images and links
    """
    if not content:
        return content
    
    # Define patterns for footer detection
    footer_patterns = [
        # Copyright patterns - match © year followed by author/company name
        r'©\s*\d{4}\s*<span[^>]*>.*?</span>',
        r'©\s*\d{4}\s*[^<\n]+(?:<br\s*/?>|\n)',
        
        # Address patterns (e.g., "548 Market Street PMB 72296, San Francisco, CA 94104")
        r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)(?:\s+PMB\s+\d+)?[,\s]+[A-Za-z\s]+,?\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?',
        
        # Substack specific unsubscribe/disable email links
        r'<a[^>]*href=["\']https://substack\.com/redirect/[^"\']*disable_email[^"\']*["\'][^>]*>.*?</a>',
        r'<a[^>]*href=["\']https://[^"\']*\.substack\.com/action/disable_email[^"\']*["\'][^>]*>.*?</a>',
        
        # "Start writing" button images and links
        r'<a[^>]*>\s*<img[^>]*(?:Start writing|publish-button)[^>]*>\s*</a>',
        r'!\[Start writing\]\([^)]+\)',
        
        # "Get the app" button images and links
        r'<a[^>]*>\s*<img[^>]*(?:Get the app|generic-app-button)[^>]*>\s*</a>',
        r'!\[Get the app\]\([^)]+\)',
        
        # Standalone promotional images
        r'<img[^>]*(?:publish-button|generic-app-button)[^>]*>',
        r'!\[(?:Start writing|Get the app)\]\([^)]+\)',
        
        # Substack redirect links
        r'<a[^>]*href=["\']https://substack\.com/redirect/[^"\']*signup[^"\']*["\'][^>]*>.*?</a>',
    ]
    
    # First, try to find where the footer starts
    # Look for copyright symbol as the main indicator
    copyright_match = re.search(r'©\s*\d{4}', content)
    
    if copyright_match:
        # Found copyright, remove everything from this point onwards
        footer_start = copyright_match.start()
        
        # Check if there's substantial content before the copyright
        # (to avoid removing the entire article if © appears early)
        if footer_start > 500:  # Only remove if copyright appears after 500 chars
            content = content[:footer_start].rstrip()
        else:
            # Copyright appears too early, try pattern-based removal instead
            for pattern in footer_patterns:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
    else:
        # No copyright found, still try to remove promotional content
        for pattern in footer_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up any trailing whitespace, empty links, or broken markdown
    content = re.sub(r'\n{3,}', '\n\n', content)  # Remove excessive newlines
    content = re.sub(r'<a[^>]*>\s*</a>', '', content)  # Remove empty links
    content = re.sub(r'<span[^>]*>\s*</span>', '', content)  # Remove empty spans
    content = re.sub(r'(?:<br\s*/?>)+$', '', content)  # Remove trailing <br> tags
    
    return content.strip()

class GmailSubstackCollector:
    """Collect Substack newsletters from Gmail"""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session or next(get_db())
        self.service = None
        # Markdownify options for better conversion
        self.markdown_options = {
            'heading_style': 'ATX',  # Use # for headings
            'bullets': '-',  # Use - for bullets
            'strong_em_symbol': '**',  # Use ** for bold
            'wrap': False,  # Don't wrap lines
            'strip': ['script', 'style', 'meta', 'noscript']  # Remove these tags
        }
        
    def authenticate(self, credentials_file: str = 'credentials.json', token_file: str = 'token.pickle'):
        """Authenticate with Gmail API"""
        creds = None
        token_path = Path(token_file)
        
        # Load existing token
        if token_path.exists():
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not Path(credentials_file).exists():
                    raise FileNotFoundError(
                        f"Gmail credentials file not found: {credentials_file}\n"
                        "Please follow these steps:\n"
                        "1. Go to https://console.cloud.google.com/\n"
                        "2. Create a new project or select existing\n"
                        "3. Enable Gmail API\n"
                        "4. Create OAuth 2.0 credentials\n"
                        "5. Download credentials.json to this directory"
                    )
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        return True
    
    def search_substack_emails(self, query: str = 'from:substack.com OR "from Marcus on AI" OR "from One Useful Thing"', max_results: int = 100) -> List[str]:
        """Search for Substack emails in Gmail"""
        try:
            # You can customize the query:
            # - 'from:substack.com' - all Substack emails
            # - 'from:substack.com is:unread' - only unread
            # - 'from:substack.com after:2024/1/1' - after specific date
            # - 'label:Substack' - if you've labeled them
            
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            # Get additional pages if needed
            while 'nextPageToken' in results and len(messages) < max_results:
                page_token = results['nextPageToken']
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=min(100, max_results - len(messages)),
                    pageToken=page_token
                ).execute()
                messages.extend(results.get('messages', []))
            
            return [msg['id'] for msg in messages]
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def get_email_content(self, msg_id: str) -> Dict:
        """Get email content and metadata"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            # Extract metadata from headers
            headers = message['payload'].get('headers', [])
            header_dict = {h['name']: h['value'] for h in headers}
            
            # Get email metadata
            subject = header_dict.get('Subject', '')
            sender = header_dict.get('From', '')
            date_str = header_dict.get('Date', '')
            
            # Parse date
            try:
                # Gmail date format: "Thu, 7 Nov 2024 08:30:00 +0000"
                from email.utils import parsedate_to_datetime
                date = parsedate_to_datetime(date_str)
            except:
                date = datetime.now(timezone.utc)
            
            # Extract HTML body
            html_body = self._extract_html_body(message['payload'])
            
            # Parse Substack-specific metadata
            author_info = self._parse_author_from_sender(sender, html_body)
            
            # Check if article already exists first (to suppress warnings on re-collection)
            substack_id = f"gmail_{msg_id}"
            existing = self.db.query(SubstackArticle).filter_by(substack_id=substack_id).first()
            
            # Clean forwarded email artifacts before parsing
            cleaned_html = self._clean_forwarded_content(html_body)
            # Pass check_only=True if article already exists to suppress warnings
            article_info = self._parse_substack_html(cleaned_html, check_only=(existing is not None))
            
            return {
                'id': msg_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'html_body': html_body,
                'author': author_info,
                'article': article_info
            }
            
        except HttpError as error:
            print(f"Error fetching message {msg_id}: {error}")
            return None
    
    def _extract_html_body(self, payload) -> str:
        """Extract HTML body from email payload"""
        html_body = ""
        
        # Check if it's multipart
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/html':
                    data = part['body']['data']
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
                elif 'parts' in part:
                    # Nested multipart
                    html_body = self._extract_html_body(part)
                    if html_body:
                        break
        else:
            # Single part message
            if payload['body'].get('data'):
                html_body = base64.urlsafe_b64decode(
                    payload['body']['data']).decode('utf-8', errors='ignore')
        
        return html_body
    
    def _parse_author_from_sender(self, sender: str, email_body: str = None) -> Dict:
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
    
    def _clean_forwarded_content(self, html_body: str) -> str:
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
            except:
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
    
    def _parse_substack_html(self, html_body: str, check_only: bool = False) -> Dict:
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
                markdown = self._clean_markdown(markdown)
                
                # Remove Substack footer content
                markdown = remove_substack_footer(markdown)
                
                # Validate content quality and clean invisible characters
                markdown = self._validate_and_fix_content(markdown, is_forwarded, check_only)
                
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
                    except:
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
                except:
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
            print(f"Error converting HTML to markdown: {e}")
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
        markdown = self._clean_markdown(markdown)
        
        # Remove Substack footer content (copyright, promotional buttons, etc.)
        markdown = remove_substack_footer(markdown)
        
        # Validate content quality and clean invisible characters
        markdown = self._validate_and_fix_content(markdown, is_forwarded, check_only)
        
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
    
    def _validate_and_fix_content(self, markdown: str, is_forwarded: bool, check_only: bool = False) -> str:
        """
        Validate that we have actual article content and fix if needed
        
        Args:
            markdown: The converted markdown
            is_forwarded: Whether this was a forwarded email
            check_only: If True, suppress warnings (used when checking existing articles)
            
        Returns:
            Validated and potentially fixed markdown
        """
        if not markdown:
            return markdown
        
        # First, clean invisible characters from the markdown
        # This ensures word counts are accurate and content is clean
        # Note: ͏ is U+034F (COMBINING GRAPHEME JOINER)
        markdown = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF\u00A0\u034F]+', ' ', markdown)
        # Preserve line breaks while cleaning extra spaces within lines
        lines = markdown.split('\n')
        cleaned_lines = []
        for line in lines:
            # Clean extra spaces within each line
            cleaned_line = re.sub(r'\s+', ' ', line).strip()
            cleaned_lines.append(cleaned_line)
        markdown = '\n'.join(cleaned_lines)
        
        # Check for common artifacts that indicate bad conversion
        bad_patterns = [
            r'^\s*:::',  # CSS/div markers
            r'^\s*\|\s*\|\s*$',  # Empty table rows
            r'\{[^}]{20,}\}',  # Long CSS blocks
            r'outlook-id=',  # Outlook artifacts
            r'style=.*font-family',  # Inline styles
            r'#[a-z0-9-]{30,}',  # Long CSS IDs
        ]
        
        # Count how many bad patterns we find
        bad_pattern_count = 0
        for pattern in bad_patterns:
            if re.search(pattern, markdown[:1000], re.MULTILINE | re.IGNORECASE):
                bad_pattern_count += 1
        
        # If we have too many artifacts, the conversion failed
        if bad_pattern_count >= 3:
            if not check_only:
                print("  ⚠️  Detected poor conversion quality, applying aggressive text extraction...")
            
            # Use aggressive cleaner directly on the markdown to extract just text
            cleaner = AggressiveHTMLCleaner()
            # Convert markdown back to simple HTML for cleaning
            simple_html = markdown.replace('\n', '<br>')
            clean_text = cleaner.extract_clean_text(f"<html><body>{simple_html}</body></html>")
            
            if clean_text and len(clean_text.split()) > 50:
                markdown = clean_text
                # Clean the extracted text as well
                markdown = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF\u00A0\u034F]+', ' ', markdown)
                # Preserve line breaks while cleaning extra spaces within lines
                lines = markdown.split('\n')
                cleaned_lines = []
                for line in lines:
                    cleaned_line = re.sub(r'\s+', ' ', line).strip()
                    cleaned_lines.append(cleaned_line)
                markdown = '\n'.join(cleaned_lines)
            else:
                if not check_only:
                    print("  ❌ Could not extract meaningful content from article")
        
        # Validation: check if we have actual content
        words = markdown.split()
        
        if len(words) < 50 and not check_only:
            print(f"  ⚠️  Article seems too short ({len(words)} words)")
        
        # Check if content is mostly formatting/artifacts
        actual_text = re.sub(r'[^a-zA-Z0-9\s]', '', markdown)
        if len(actual_text) < len(markdown) * 0.3 and not check_only:  # Less than 30% actual text
            print("  ⚠️  Article contains mostly formatting/special characters")
        
        return markdown
    
    def _clean_markdown(self, markdown: str) -> str:
        """Clean up converted markdown and remove table artifacts"""
        if not markdown:
            return ""
        
        # First pass: Remove leading pipe prefixes from lines
        lines = markdown.split('\n')
        depipe_lines = []
        for line in lines:
            # Remove leading pipes while preserving content
            # Patterns like "| | | content" become just "content"
            cleaned_line = re.sub(r'^\s*\|+(\s*\|)*\s*', '', line)
            
            # If line becomes empty after removing pipes, check if it was originally empty
            if cleaned_line.strip() == '' and line.strip() != '':
                # This was a line with just pipes, skip it
                continue
            depipe_lines.append(cleaned_line)
        
        # Second pass: Clean image tables (remove pipes around images and their separators)
        lines = depipe_lines
        image_cleaned_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Check if this line is an image wrapped in table formatting
            if re.match(r'^\|?\s*!\[.*?\]\(.*?\)\s*\|?\s*$', stripped):
                # Extract just the image markdown
                image_match = re.search(r'!\[.*?\]\(.*?\)', line)
                if image_match:
                    image_cleaned_lines.append(image_match.group(0))
                    # Check if next line is a separator and skip it
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if ('---|' in next_line or '|---' in next_line or 
                            re.match(r'^[\s\-\|]+$', next_line)):
                            i += 1  # Skip the separator
                i += 1
                continue
            
            # Keep the line for further processing
            image_cleaned_lines.append(line)
            i += 1
        
        # Third pass: Remove other table artifacts
        lines = image_cleaned_lines
        cleaned_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Skip table separator lines (---|---|--- patterns)
            if ('---|' in stripped or '|---' in stripped or 
                re.match(r'^[\s\-\|]+$', stripped) and '---' in stripped and '|' in stripped):
                # Check if previous line has an image (keep separator if part of image table)
                if i > 0 and '![' in lines[i-1]:
                    cleaned_lines.append(line)
                else:
                    i += 1
                    continue  # Skip this separator
                i += 1
                continue
            
            # Skip lone pipe characters or pipes with just spaces
            if re.match(r'^\|+\s*\|*\s*\|*$', stripped) or stripped == '|':
                i += 1
                continue
            
            # Skip lines that are just pipes and spaces (like "| |" or "| | |")
            if re.match(r'^[\|\s]+$', stripped) and '|' in stripped:
                i += 1
                continue
            
            # Skip lines that are just dashes (but not markdown headers)
            if stripped in ['---', '----', '-----', '------'] or re.match(r'^-+$', stripped):
                # Check if this might be a markdown horizontal rule (needs blank line before)
                # Also check if it's between image links (part of image layout)
                is_hr = i > 0 and lines[i-1].strip() == ''
                is_image_separator = (i > 0 and '![' in lines[i-1]) or (i < len(lines) - 1 and '![' in lines[i+1])
                
                if is_hr and not is_image_separator:
                    # This is a legitimate horizontal rule, keep it
                    cleaned_lines.append(line)
                elif is_image_separator:
                    # This is part of image layout, skip it
                    pass
                # Skip this artifact
                i += 1
                continue
            
            # Skip multiple consecutive separator lines
            if re.match(r'^-+\s*$', stripped) and len(stripped) > 5:
                # Check context
                if i > 0 and i < len(lines) - 1:
                    prev_line = lines[i-1].strip()
                    next_line = lines[i+1].strip() if i+1 < len(lines) else ''
                    
                    # If surrounded by similar lines, it's probably a table artifact
                    if re.match(r'^-+\s*$', prev_line) or re.match(r'^-+\s*$', next_line):
                        i += 1
                        continue
                
                # Otherwise keep it
                cleaned_lines.append(line)
            else:
                # Keep all other lines
                cleaned_lines.append(line)
            
            i += 1
        
        # Join lines back
        markdown = '\n'.join(cleaned_lines)
        
        # Remove excessive newlines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Remove invisible Unicode characters
        markdown = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF]+', '', markdown)
        markdown = re.sub(r'[\u00A0]+', ' ', markdown)
        
        # Remove the weird invisible character strings
        markdown = re.sub(r'(͏\s*)+', '', markdown)
        
        # Remove email footer stuff
        patterns_to_remove = [
            r'Unsubscribe.*?$',
            r'View this email in your browser.*?$',
            r'You received this email because.*?$',
            r'Update your email preferences.*?$'
        ]
        
        for pattern in patterns_to_remove:
            markdown = re.sub(pattern, '', markdown, flags=re.MULTILINE | re.IGNORECASE)
        
        return markdown.strip()
    
    def save_article(self, email_data: Dict) -> Optional[SubstackArticle]:
        """Save article to database"""
        if not email_data or not email_data.get('article'):
            return None
        
        # Validate that this is from an expected author (configured authors + direct Substack subscriptions)
        author_info = email_data['author']
        expected_emails = ['robotic@substack.com', 'garymarcus@substack.com', 'sebastianraschka@substack.com']
        
        # Also allow direct Substack subscriptions (emails ending with @substack.com)
        is_direct_substack = author_info['email'].endswith('@substack.com')
        is_configured_forwarded = author_info['email'] in expected_emails
        
        if not (is_direct_substack or is_configured_forwarded):
            print(f"  ⚠️  Skipping article from unexpected author: {author_info['name']} ({author_info['email']})")
            return None
        
        # Get or create author
        author_info = email_data['author']
        author = self.db.query(SubstackAuthor).filter_by(
            subdomain=author_info['subdomain']
        ).first()
        
        if not author:
            author = SubstackAuthor(
                subdomain=author_info['subdomain'],
                name=author_info['name'],
                email=author_info.get('email'),
                url=f"https://{author_info['subdomain']}.substack.com"
            )
            self.db.add(author)
            self.db.flush()
        
        # Check if article already exists
        article_data = email_data['article']
        
        # Create unique ID from email ID
        substack_id = f"gmail_{email_data['id']}"
        
        existing = self.db.query(SubstackArticle).filter_by(
            substack_id=substack_id
        ).first()
        
        if existing:
            if existing.deleted:
                # Check if we should restore deleted articles
                import sys
                restore_deleted = '--restore-deleted' in sys.argv
                
                if restore_deleted:
                    print(f"  🔄 Restoring deleted article: {article_data.get('title', 'Untitled')}")
                    existing.deleted = False
                    # Update the content with the new parsed data
                    existing.content_markdown = article_data.get('content_markdown')
                    existing.content_html = article_data.get('content_html')
                    existing.preview = article_data.get('preview')
                    existing.word_count = article_data.get('word_count')
                    existing.reading_time_minutes = article_data.get('reading_time_minutes')
                    if article_data.get('url'):
                        existing.url = article_data.get('url')
                    self.db.commit()
                    return existing
                else:
                    print(f"Article was deleted by user, skipping: {article_data.get('title', 'Untitled')}")
                    return None
            print(f"Article already exists: {article_data.get('title', 'Untitled')}")
            # Update the article if it has no content but we now have content
            if (not existing.content_markdown or existing.word_count == 0) and article_data.get('content_markdown'):
                print(f"  📝 Updating empty article with new content ({article_data.get('word_count', 0)} words)")
                existing.content_markdown = article_data.get('content_markdown')
                existing.content_html = article_data.get('content_html')
                existing.preview = article_data.get('preview')
                existing.word_count = article_data.get('word_count', 0)
                existing.reading_time_minutes = article_data.get('reading_time_minutes', 1)
                if article_data.get('url'):
                    existing.url = article_data.get('url')
                self.db.commit()
            return existing
        
        # Create new article
        # For forwarded emails, always use the email subject as title
        article_title = article_data.get('title')
        if not article_title or article_title in ['Untitled', 'Forwarded Newsletter', 'Use Email Subject']:
            # Use email subject, cleaning up any forward prefixes
            subject = email_data['subject']
            # Remove common forward prefixes
            for prefix in ['Fwd: ', 'FW: ', 'Re: ', 'RE: ']:
                if subject.startswith(prefix):
                    subject = subject[len(prefix):]
            article_title = subject if subject else 'Untitled'
        
        # Clean footer from HTML content too
        content_html = article_data.get('content_html')
        if content_html:
            content_html = remove_substack_footer(content_html)
        
        article = SubstackArticle(
            substack_id=substack_id,
            title=article_title,
            subtitle=article_data.get('subtitle'),
            url=article_data.get('url'),
            content_html=content_html,
            content_markdown=article_data.get('content_markdown'),
            preview=article_data.get('preview'),
            word_count=article_data.get('word_count', 0),
            reading_time_minutes=article_data.get('reading_time_minutes', 1),
            author_id=author.id,
            published_at=email_data['date'],
            collected_at=datetime.now(timezone.utc)
        )
        
        self.db.add(article)
        return article
    
    def collect_newsletters(self, query: str = None, max_results: int = 50) -> int:
        """Main collection method"""
        print(f"🔍 Searching for Substack newsletters...")
        
        # Create collection record
        collection = SubstackCollection(
            source='email',
            status='running'
        )
        self.db.add(collection)
        self.db.flush()
        
        try:
            # Authenticate if needed
            if not self.service:
                print("📧 Authenticating with Gmail...")
                self.authenticate()
            
            # Search for emails - use expanded query if none provided
            if query is None:
                # Include emails from your UniSG account that contain Substack forwards
                # For forwarded emails, we search by sender and content, not subject
                
                # Load forwarded authors from config for comprehensive search
                config_path = Path(__file__).parent.parent.parent / 'forwarded_authors.json'
                author_emails = []
                
                if config_path.exists():
                    try:
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                            author_emails = [
                                f'"{author["email"]}"' 
                                for author in config.get('forwarded_authors', [])
                            ]
                    except Exception:
                        pass  # Silently fall back to basic search
                
                # Build comprehensive query - be more specific for forwarded emails
                query_parts = [
                    'from:substack.com',
                    '(from:siegfried.handschuh@unisg.ch AND substack)', 
                    '(from:me to:me AND substack)',
                    '"@substack.com"'
                ]
                query_parts.extend(author_emails)
                
                query = ' OR '.join(query_parts)
            
            message_ids = self.search_substack_emails(query, max_results)
            print(f"📬 Found {len(message_ids)} Substack emails")
            
            # Process each email
            articles_saved = 0
            for i, msg_id in enumerate(message_ids, 1):
                print(f"\n📖 Processing email {i}/{len(message_ids)}...")
                
                # Get email content
                email_data = self.get_email_content(msg_id)
                if not email_data:
                    continue
                
                # Save to database
                article = self.save_article(email_data)
                if article:
                    articles_saved += 1
                    print(f"  ✅ Saved: {article.title[:60]}...")
                
                # Commit periodically
                if i % 10 == 0:
                    self.db.commit()
            
            # Final commit
            self.db.commit()
            
            # Update collection record
            collection.completed_at = datetime.now(timezone.utc)
            collection.articles_collected = articles_saved
            collection.status = 'completed'
            self.db.commit()
            
            print(f"\n✅ Collection complete! Saved {articles_saved} new articles")
            return articles_saved
            
        except Exception as e:
            print(f"❌ Error during collection: {e}")
            collection.status = 'failed'
            collection.error_message = str(e)
            self.db.commit()
            raise

# Helper function for command-line usage
def main():
    """Run the collector from command line"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect Substack newsletters from Gmail')
    parser.add_argument('--query', default=None, 
                       help='Gmail search query (default: comprehensive search)')
    parser.add_argument('--max', type=int, default=50,
                       help='Maximum emails to process (default: 50)')
    parser.add_argument('--setup', action='store_true',
                       help='Run initial Gmail authentication setup')
    parser.add_argument('--forwarded', action='store_true',
                       help='Search only for forwarded emails from configured authors')
    parser.add_argument('--after', default=None,
                       help='Collect emails after this date (format: YYYY-MM-DD, e.g., 2025-08-11)')
    parser.add_argument('--before', default=None,
                       help='Collect emails before this date (format: YYYY-MM-DD, e.g., 2025-08-12)')
    parser.add_argument('--on', default=None,
                       help='Collect emails on this specific date (format: YYYY-MM-DD, e.g., 2025-08-11)')
    parser.add_argument('--days', type=int, default=None,
                       help='Collect emails from the last N days (e.g., --days 2 for last 2 days)')
    parser.add_argument('--restore-deleted', action='store_true',
                       help='Restore and re-import soft-deleted articles (undelete them)')
    
    args = parser.parse_args()
    
    collector = GmailSubstackCollector()
    
    if args.setup:
        print("🔐 Setting up Gmail authentication...")
        print("This will open a browser window for you to authorize access.")
        collector.authenticate()
        print("✅ Authentication successful! Token saved.")
    else:
        # Build query based on flags
        query_parts = []
        
        # Add date filters if specified
        from datetime import datetime, timedelta
        
        if args.days:
            # Calculate date range from --days parameter
            today = datetime.now()
            days_ago = (today - timedelta(days=args.days)).strftime('%Y-%m-%d')
            query_parts.append(f'after:{days_ago}')
            print(f"📅 Collecting emails from the last {args.days} days (since {days_ago})")
        elif args.on:
            # Specific date - use after and before to bracket the day
            query_parts.append(f'after:{args.on}')
            # Add one day for before (Gmail date logic)
            date_obj = datetime.strptime(args.on, '%Y-%m-%d')
            next_day = (date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
            query_parts.append(f'before:{next_day}')
            print(f"📅 Collecting emails from {args.on}")
        else:
            if args.after:
                query_parts.append(f'after:{args.after}')
                print(f"📅 Collecting emails after {args.after}")
            if args.before:
                query_parts.append(f'before:{args.before}')
                print(f"📅 Collecting emails before {args.before}")
        
        # Build base query
        if args.query:
            base_query = args.query
        elif args.forwarded:
            # Search only for forwarded emails from configured authors
            print("🔄 Searching only for forwarded emails from configured authors...")
            
            # Load forwarded authors from config
            config_path = Path(__file__).parent.parent.parent / 'forwarded_authors.json'
            author_emails = []
            
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        author_emails = [
                            f'"{author["email"]}"' 
                            for author in config.get('forwarded_authors', [])
                        ]
                        print(f"Loaded {len(author_emails)} configured authors")
                except Exception as e:
                    print(f"Warning: Could not load forwarded_authors.json: {e}")
            else:
                print("Warning: forwarded_authors.json not found")
            
            # Build query with dynamic author emails - be very specific for forwarded emails
            # Only search for forwarded emails that contain the actual configured author names/emails
            forward_query_parts = []
            
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        for author in config.get('forwarded_authors', []):
                            # Search for forwarded emails that contain this specific author's name or email
                            forward_query_parts.extend([
                                f'(from:siegfried.handschuh@unisg.ch AND "{author["name"]}")',
                                f'(from:siegfried.handschuh@unisg.ch AND "{author["email"]}")',
                                f'(from:me to:me AND "{author["name"]}")',
                                f'(from:me to:me AND "{author["email"]}")'
                            ])
                except Exception:
                    pass
            
            # Combine forwarded query parts
            forwarded_base = ' OR '.join(forward_query_parts + author_emails)
            base_query = f'({forwarded_base})'
        else:
            # Default comprehensive Substack search
            base_query = 'from:substack OR from:@substack.com'
        
        # Combine base query with date filters
        if query_parts:  # Has date filters
            date_filters = ' '.join(query_parts)
            query = f'{base_query} {date_filters}'
        else:
            query = base_query
        
        print(f"📧 Final query: {query[:100]}...")
        
        articles = collector.collect_newsletters(query, args.max)
        
        # Show summary
        db = next(get_db())
        total_articles = db.query(SubstackArticle).count()
        total_authors = db.query(SubstackAuthor).count()
        
        print(f"\n📊 Database Summary:")
        print(f"  Total articles: {total_articles}")
        print(f"  Total authors: {total_authors}")

if __name__ == "__main__":
    main()