"""
Aggressive HTML Cleaner for Substack Articles
Removes all formatting and extracts only the actual content
"""
import re
from bs4 import BeautifulSoup, NavigableString
from typing import Optional


class AggressiveHTMLCleaner:
    """Aggressively clean HTML to extract only content"""
    
    def extract_clean_text(self, html_content: str) -> str:
        """
        Extract only the actual text content from HTML, removing all formatting
        
        Args:
            html_content: Raw HTML
            
        Returns:
            Clean text content suitable for markdown conversion
        """
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Step 1: Remove all script, style, meta, and other non-content tags
        for tag in soup(['script', 'style', 'meta', 'link', 'noscript', 'head']):
            tag.decompose()
        
        # Step 2: Remove all CSS classes and styles
        for tag in soup.find_all():
            # Remove all attributes except href for links and src/alt for images
            if tag.name == 'a':
                href = tag.get('href', '')
                tag.attrs = {'href': href} if href else {}
            elif tag.name == 'img':
                src = tag.get('src', '')
                alt = tag.get('alt', '')
                tag.attrs = {'src': src, 'alt': alt}
            else:
                tag.attrs = {}
        
        # Step 3: Remove divs and spans that only contain formatting
        self._unwrap_formatting_containers(soup)
        
        # Step 4: Extract and clean the content
        content = self._extract_article_content(soup)
        
        return content
    
    def _unwrap_formatting_containers(self, soup: BeautifulSoup):
        """Remove unnecessary container elements while preserving content"""
        # Tags to completely unwrap (keep content, remove tag)
        unwrap_tags = ['span', 'font', 'center', 'small', 'big']
        
        for tag_name in unwrap_tags:
            for tag in soup.find_all(tag_name):
                tag.unwrap()
        
        # Convert divs that only contain text or other simple elements
        for div in soup.find_all('div'):
            # Check if div contains actual content
            if self._is_content_div(div):
                # Keep the div but remove its attributes
                div.attrs = {}
            else:
                # Unwrap formatting-only divs
                div.unwrap()
    
    def _is_tracking_image(self, src: str, img_element) -> bool:
        """Check if an image is a tracking pixel or should be skipped"""
        if not src:
            return True
            
        # Check for tracking pixels by URL patterns
        tracking_patterns = [
            'open?token=',
            '/track',
            'pixel',
            '/spacer',
            '1x1',
            'blank.gif',
            'data:image/gif;base64,R0lGOD'  # 1x1 transparent GIFs
        ]
        
        for pattern in tracking_patterns:
            if pattern in src.lower():
                return True
        
        # Check by dimensions if available
        width = img_element.get('width', '')
        height = img_element.get('height', '')
        
        if width and height:
            try:
                w = int(width) if isinstance(width, str) else width
                h = int(height) if isinstance(height, str) else height
                if w <= 2 and h <= 2:  # 1x1 or 2x2 pixels
                    return True
                if w <= 20 and h <= 20 and 'substack-post-media' not in src:
                    # Small images that aren't content
                    return True
            except:
                pass
        
        return False
    
    def _is_content_div(self, element) -> bool:
        """Check if an element contains actual content"""
        # Get text content
        text = element.get_text(strip=True)
        
        # Check if it's just formatting/metadata
        if not text or len(text) < 20:
            return False
        
        # Check for forwarding headers
        if any(marker in text[:100] for marker in ['From:', 'Date:', 'Subject:', 'To:', 'Sent:']):
            return False
        
        # Check for UI elements
        if any(marker in text.lower() for marker in ['view in browser', 'unsubscribe', 'manage preferences', 'share', 'like', 'comment']):
            return False
        
        return True
    
    def _extract_article_content(self, soup: BeautifulSoup) -> str:
        """Extract the main article content from the soup"""
        content_parts = []
        
        # Look for the main content area
        # Try to find article tag first
        article = soup.find('article')
        if article:
            soup = article
        
        # Extract title if present
        title = None
        for heading_tag in ['h1', 'h2', 'h3']:
            heading = soup.find(heading_tag)
            if heading:
                heading_text = heading.get_text(strip=True)
                if heading_text and len(heading_text) > 5 and not any(x in heading_text for x in ['From:', 'Date:', 'Subject:']):
                    title = heading_text
                    break
        
        if title:
            content_parts.append(f"# {title}\n")
        
        # Extract paragraphs, images, and other content IN ORDER
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'ul', 'ol', 'li', 'pre', 'code', 'img', 'figure']):
            # Handle images
            if element.name == 'img':
                src = element.get('src', '')
                alt = element.get('alt', '')
                
                # Skip tracking pixels and tiny images
                if self._is_tracking_image(src, element):
                    continue
                
                # Add image in markdown format
                if src:
                    # Clean up the URL if needed
                    if 'substackcdn.com' in src and 'substack-post-media' in src:
                        # This is a real content image from Substack
                        content_parts.append(f"\n![{alt or 'Image'}]({src})\n")
                    elif src.startswith('http'):
                        # Other web images
                        content_parts.append(f"\n![{alt or 'Image'}]({src})\n")
                continue
            
            # Handle figure elements (may contain images with captions)
            if element.name == 'figure':
                img = element.find('img')
                if img:
                    src = img.get('src', '')
                    alt = img.get('alt', '')
                    if src and not self._is_tracking_image(src, img):
                        content_parts.append(f"\n![{alt or 'Image'}]({src})\n")
                        
                        # Look for caption
                        caption = element.find('figcaption')
                        if caption:
                            caption_text = caption.get_text(strip=True)
                            if caption_text:
                                content_parts.append(f"*{caption_text}*\n")
                continue
            
            text = element.get_text(strip=True)
            
            # Skip empty or very short elements
            if not text or len(text) < 3:
                continue
            
            # Skip forwarding headers
            if any(marker in text for marker in ['From:', 'Date:', 'Subject:', 'To:', 'Sent:', 'View in browser']):
                continue
            
            # Skip UI elements
            if text.lower() in ['share', 'like', 'comment', 'restack', 'subscribe', 'unsubscribe', 'read in app']:
                continue
            
            # Format based on tag type
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                content_parts.append(f"\n{'#' * level} {text}\n")
            elif element.name == 'blockquote':
                content_parts.append(f"\n> {text}\n")
            elif element.name == 'li':
                # Check if it's part of an ordered or unordered list
                parent = element.parent
                if parent and parent.name == 'ol':
                    # For ordered lists, we'd need to track the number
                    content_parts.append(f"1. {text}")
                else:
                    content_parts.append(f"* {text}")
            elif element.name == 'pre' or element.name == 'code':
                content_parts.append(f"\n```\n{text}\n```\n")
            else:
                # Regular paragraph
                content_parts.append(f"{text}\n")
        
        # Join and clean up
        content = '\n'.join(content_parts)
        
        # Remove multiple consecutive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove any remaining artifacts
        content = self._clean_text_artifacts(content)
        
        return content.strip()
    
    def _clean_text_artifacts(self, text: str) -> str:
        """Clean common text artifacts"""
        # Remove CSS class references
        text = re.sub(r'\{[^}]*\}', '', text)
        text = re.sub(r':+\s*\{[^}]*\}', '', text)
        
        # Remove style attributes that leaked through
        text = re.sub(r'style="[^"]*"', '', text)
        text = re.sub(r'class="[^"]*"', '', text)
        
        # Remove outlook IDs
        text = re.sub(r'outlook-id="[^"]*"', '', text)
        
        # Remove component names
        text = re.sub(r'component-name="[^"]*"', '', text)
        
        # Remove data attributes
        text = re.sub(r'data-[a-z-]+="[^"]*"', '', text, flags=re.IGNORECASE)
        
        # Remove empty brackets and pipes
        text = re.sub(r'\[\s*\]', '', text)
        text = re.sub(r'\|\s*\|', '', text)
        text = re.sub(r'\|\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\|', '', text, flags=re.MULTILINE)
        
        # Remove ::: markers
        text = re.sub(r'^:::+.*$', '', text, flags=re.MULTILINE)
        
        # Remove repeated dashes or underscores (likely separators)
        text = re.sub(r'^[-_]{3,}$', '', text, flags=re.MULTILINE)
        
        # Clean up whitespace
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines to double
        
        return text


def clean_substack_html(html_content: str) -> str:
    """
    Convenience function to clean Substack HTML
    
    Args:
        html_content: Raw HTML from Substack email
        
    Returns:
        Clean text ready for markdown conversion
    """
    cleaner = AggressiveHTMLCleaner()
    return cleaner.extract_clean_text(html_content)