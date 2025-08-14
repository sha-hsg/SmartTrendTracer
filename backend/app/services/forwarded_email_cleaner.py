"""
Forwarded Email Cleaner Service
Removes forwarding headers and artifacts from emails while preserving content
"""
import re
from typing import Optional
from bs4 import BeautifulSoup


class ForwardedEmailCleaner:
    """Clean forwarded email headers and artifacts"""
    
    # Common forwarding header patterns
    FORWARD_HEADER_PATTERNS = [
        # Outlook/Exchange patterns
        r'From:\s*[^<\n]+<[^>]+>',
        r'Sent:\s*\w+,\s*\w+\s*\d+,\s*\d{4}',
        r'To:\s*[^<\n]+<[^>]+>',
        r'Subject:\s*.+',
        r'Date:\s*\w+,\s*\d+\s*\w+\s*\d{4}',
        
        # Common forward indicators
        r'-+\s*Original Message\s*-+',
        r'-+\s*Forwarded message\s*-+',
        r'Begin forwarded message:',
        r'---------- Forwarded message ----------',
        
        # Email metadata
        r'Reply-To:\s*.+',
        r'CC:\s*.+',
        r'BCC:\s*.+',
        r'Importance:\s*.+',
        r'X-[A-Za-z-]+:\s*.+',  # X-Headers
    ]
    
    def clean_html(self, html_content: str) -> str:
        """
        Clean forwarded email HTML content
        
        Args:
            html_content: Raw HTML from email
            
        Returns:
            Cleaned HTML with forwarding headers removed
        """
        if not html_content:
            return html_content
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Remove Outlook mobile reference divs
        for div in soup.find_all('div', class_='ms-outlook-mobile-reference-message'):
            div.decompose()
        
        # 2. Remove elements containing only forwarding metadata
        self._remove_forward_header_elements(soup)
        
        # 3. Remove tracking pixels and tiny images
        self._remove_tracking_images(soup)
        
        # 4. Clean up empty elements left behind
        self._remove_empty_elements(soup)
        
        return str(soup)
    
    def clean_markdown(self, markdown_text: str) -> str:
        """
        Clean forwarded email artifacts from markdown
        
        Args:
            markdown_text: Markdown content
            
        Returns:
            Cleaned markdown
        """
        if not markdown_text:
            return markdown_text
        
        # Split into lines for processing
        lines = markdown_text.split('\n')
        cleaned_lines = []
        skip_until_content = False
        found_content = False
        
        for i, line in enumerate(lines):
            # Check if this line is a forwarding header
            if self._is_forward_header_line(line):
                skip_until_content = True
                continue
            
            # Check if we've found actual content
            if skip_until_content and self._is_content_line(line):
                skip_until_content = False
                found_content = True
            
            # Add line if we're not skipping or if we've found content
            if not skip_until_content or found_content:
                # Additional cleaning for markdown artifacts
                cleaned_line = self._clean_markdown_line(line)
                if cleaned_line is not None:
                    cleaned_lines.append(cleaned_line)
        
        # Join and do final cleanup
        markdown = '\n'.join(cleaned_lines)
        
        # Remove multiple consecutive blank lines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Remove forwarding patterns that might have survived
        for pattern in self.FORWARD_HEADER_PATTERNS:
            markdown = re.sub(pattern, '', markdown, flags=re.MULTILINE | re.IGNORECASE)
        
        return markdown.strip()
    
    def _remove_forward_header_elements(self, soup: BeautifulSoup):
        """Remove HTML elements that contain only forwarding headers"""
        elements_to_remove = []
        
        # Check divs and tables for forwarding content
        for element in soup.find_all(['div', 'table', 'tr', 'td']):
            text = element.get_text(strip=True)
            
            # Skip if too long (likely contains real content)
            if len(text) > 500:
                continue
            
            # Check if this element contains forwarding metadata
            if self._is_forward_metadata(text):
                # Make sure we're not removing content
                # Check if element has substantial child elements
                has_content = (
                    element.find_all('p', string=lambda x: x and len(x.strip()) > 50) or
                    element.find_all('article') or
                    element.find_all('section') or
                    element.find_all(['h1', 'h2', 'h3'], string=lambda x: x and len(x.strip()) > 10)
                )
                
                if not has_content:
                    elements_to_remove.append(element)
        
        # Remove identified elements
        for element in elements_to_remove:
            element.decompose()
    
    def _remove_tracking_images(self, soup: BeautifulSoup):
        """Remove tracking pixels and tiny images"""
        for img in soup.find_all('img'):
            try:
                width = img.get('width', '')
                height = img.get('height', '')
                src = img.get('src', '')
                
                # Remove tracking pixels
                if (
                    (str(width) == '1' and str(height) == '1') or
                    'open?token=' in src or
                    '/track' in src or
                    'pixel' in src.lower() or
                    src.startswith('data:image/gif;base64,R0lGOD')  # 1x1 transparent GIFs
                ):
                    img.decompose()
                    continue
                
                # Remove very small images (likely icons)
                if width and height:
                    try:
                        w = float(width)
                        h = float(height)
                        if w <= 20 and h <= 20:
                            img.decompose()
                    except:
                        pass
            except:
                pass
    
    def _remove_empty_elements(self, soup: BeautifulSoup):
        """Remove empty divs and other elements"""
        for element in soup.find_all(['div', 'p', 'span', 'table']):
            # Check if element is effectively empty
            if not element.get_text(strip=True) and not element.find_all('img'):
                element.decompose()
    
    def _is_forward_metadata(self, text: str) -> bool:
        """Check if text appears to be forwarding metadata"""
        if not text:
            return False
        
        # Count how many forwarding indicators are present
        indicators = 0
        
        # Check for common forwarding fields
        forward_fields = ['From:', 'To:', 'Date:', 'Sent:', 'Subject:', 'FW:', 'Fwd:', 'RE:']
        for field in forward_fields:
            if field in text:
                indicators += 1
        
        # If we have multiple indicators, it's likely forwarding metadata
        if indicators >= 2:
            return True
        
        # Check for "Original Message" or similar
        if any(phrase in text.lower() for phrase in ['original message', 'forwarded message', 'begin forwarded']):
            return True
        
        return False
    
    def _is_forward_header_line(self, line: str) -> bool:
        """Check if a line is a forwarding header"""
        line = line.strip()
        
        # Empty lines are not headers
        if not line:
            return False
        
        # Check for common forwarding patterns
        forward_indicators = [
            'From:', 'To:', 'Date:', 'Sent:', 'Subject:',
            'Reply-To:', 'CC:', 'BCC:', 'Importance:',
            '----', '____', '****',  # Separator lines
            'Original Message', 'Forwarded message',
            'Begin forwarded', 'End forwarded'
        ]
        
        for indicator in forward_indicators:
            if line.startswith(indicator) or indicator.lower() in line.lower():
                return True
        
        # Check for email-like patterns
        if re.match(r'^[A-Za-z-]+:\s*.+', line):  # Header: Value format
            return True
        
        return False
    
    def _is_content_line(self, line: str) -> bool:
        """Check if a line appears to be actual content"""
        line = line.strip()
        
        # Empty lines don't count as content start
        if not line:
            return False
        
        # Must be substantial (not just a word or two)
        if len(line) < 20:
            return False
        
        # Should not be a forwarding indicator
        if self._is_forward_header_line(line):
            return False
        
        # Should not be just a link or email
        if line.startswith('http') or '@' in line and len(line.split()) <= 3:
            return False
        
        return True
    
    def _clean_markdown_line(self, line: str) -> Optional[str]:
        """Clean individual markdown line"""
        # Remove table artifacts that are just formatting
        if line.strip() in ['|', '| |', '| --- |', '|---|', '| --- | --- |']:
            return None
        
        # Remove lines that are just dashes or underscores
        if re.match(r'^[-_]{3,}$', line.strip()):
            return None
        
        # Remove "View in browser" type lines
        if any(phrase in line.lower() for phrase in ['view in browser', 'view online', 'unsubscribe', 'manage preferences']):
            return None
        
        return line


def clean_forwarded_email(html_content: str, to_markdown: bool = False) -> str:
    """
    Convenience function to clean forwarded email content
    
    Args:
        html_content: HTML content to clean
        to_markdown: If True, also clean markdown artifacts
        
    Returns:
        Cleaned content
    """
    cleaner = ForwardedEmailCleaner()
    cleaned_html = cleaner.clean_html(html_content)
    
    if to_markdown:
        # Convert to markdown first (using existing converter)
        from app.services.document_converter import DocumentConverter
        converter = DocumentConverter()
        markdown = converter.html_to_markdown(cleaned_html)
        
        # Then clean markdown artifacts
        return cleaner.clean_markdown(markdown)
    
    return cleaned_html