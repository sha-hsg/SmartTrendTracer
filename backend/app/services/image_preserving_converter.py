"""
Image-Preserving HTML to Markdown Converter
Keeps table structure to maintain image positions (trade-off: table artifacts for perfect image placement)
"""
import re
from typing import Optional
from bs4 import BeautifulSoup
import html2text


class ImagePreservingConverter:
    """
    Converter that prioritizes image preservation over clean markdown
    Keeps table structures intact to maintain image positions
    """
    
    def __init__(self):
        # Configure html2text for maximum fidelity
        self.h2t = html2text.HTML2Text()
        self.h2t.body_width = 0  # Don't wrap lines
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.images_to_alt = False  # Keep images as markdown
        self.h2t.unicode_snob = True
        self.h2t.wrap_links = False
        self.h2t.skip_internal_links = False
        self.h2t.single_line_break = False
        self.h2t.protect_links = True
        self.h2t.ignore_tables = False  # IMPORTANT: Keep tables for image positioning
    
    def convert(self, html_content: str, base_url: Optional[str] = None) -> str:
        """
        Convert HTML to markdown preserving images at exact positions
        
        Args:
            html_content: HTML string to convert
            base_url: Optional base URL for relative links
            
        Returns:
            Markdown with images preserved (includes table structure)
        """
        if not html_content:
            return ""
        
        # Preprocess HTML to clean up tracking but keep structure
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove only true tracking pixels (1x1) and scripts
        for element in soup.find_all(['script', 'style', 'meta', 'noscript']):
            element.decompose()
        
        # Process images - remove tracking but keep content images
        images_to_remove = []
        for img in soup.find_all('img'):
            width = img.get('width', '')
            height = img.get('height', '')
            src = img.get('src', '')
            
            # Convert width/height to float for comparison
            try:
                w = float(width) if width else 0
                h = float(height) if height else 0
            except:
                w = h = 0
            
            # Remove tracking pixels and small UI icons
            if (w <= 50 and h <= 50) or 'eotrx' in src.lower():
                images_to_remove.append(img)
            else:
                # This is a content image - preserve it!
                if not img.get('alt'):
                    img['alt'] = 'Article image'
                
                # If wrapped in a link, unwrap to make markdown conversion cleaner
                parent_link = img.find_parent('a')
                if parent_link:
                    # Keep the image but replace the link with just the image
                    parent_link.replace_with(img)
        
        # Now remove the tracking images
        for img in images_to_remove:
            parent_link = img.find_parent('a')
            if parent_link:
                parent_link.decompose()
            else:
                img.decompose()
        
        # Clean up empty table cells but keep structure
        for td in soup.find_all(['td', 'th']):
            # If cell only contains whitespace or nbsp, add a space
            if not td.get_text(strip=True):
                td.string = ' '
        
        # Set base URL if provided
        if base_url:
            self.h2t.baseurl = base_url
        
        # Convert to markdown, preserving tables
        markdown = self.h2t.handle(str(soup))
        
        # Post-process to clean up worst artifacts while keeping images
        markdown = self._clean_markdown(markdown)
        
        return markdown
    
    def _clean_markdown(self, markdown: str) -> str:
        """
        Clean up the worst artifacts while preserving image positions
        """
        # Remove invisible Unicode characters
        markdown = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF\u00A0]+', ' ', markdown)
        
        # Clean up excessive whitespace in table cells
        markdown = re.sub(r'\|\s{3,}\|', '|  |', markdown)
        
        # Remove completely empty table rows (but keep ones with images)
        lines = markdown.split('\n')
        cleaned_lines = []
        for i, line in enumerate(lines):
            # Skip rows that are just pipes and spaces (no content)
            if re.match(r'^\|\s*\|\s*\|\s*\|?\s*$', line):
                # Check if next line has an image
                if i + 1 < len(lines) and '![' not in lines[i + 1]:
                    continue
            cleaned_lines.append(line)
        
        markdown = '\n'.join(cleaned_lines)
        
        # Fix broken image markdown
        markdown = re.sub(r'!\[([^\]]*)\]\s+\(([^\)]+)\)', r'![\1](\2)', markdown)
        
        # Remove excessive blank lines
        markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)
        
        # Clean up table separators that are too long
        markdown = re.sub(r'(\|[\s\-]+){10,}\|', '| --- | --- | --- |', markdown)
        
        return markdown.strip()


class HybridConverter:
    """
    Hybrid approach: Extract images and content separately, then merge
    """
    
    def convert(self, html_content: str) -> str:
        """
        Extract images with context, then merge with clean text
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Step 1: Extract all content images with their surrounding text
        images_with_context = []
        for img in soup.find_all('img'):
            width = img.get('width', '')
            height = img.get('height', '')
            src = img.get('src', '')
            
            # Skip tracking pixels and UI elements
            if (str(width) in ['1', '18', '40'] or 
                str(height) in ['1', '18', '40'] or
                any(x in src.lower() for x in ['eotrx', 'track', 'pixel'])):
                continue
            
            # Get surrounding context
            parent = img.parent
            while parent and parent.name in ['span', 'a', 'td', 'div']:
                parent = parent.parent
            
            # Get text before and after
            prev_text = ''
            next_text = ''
            
            if parent:
                # Get previous sibling text
                prev = parent.previous_sibling
                while prev and not prev.string:
                    prev = prev.previous_sibling
                if prev:
                    prev_text = str(prev.string or '')[-100:]
                
                # Get next sibling text
                next = parent.next_sibling
                while next and not next.string:
                    next = next.next_sibling
                if next:
                    next_text = str(next.string or '')[:100]
            
            images_with_context.append({
                'src': src,
                'alt': img.get('alt', 'Image'),
                'before': prev_text.strip(),
                'after': next_text.strip(),
                'paragraph': parent.get_text(strip=True) if parent else ''
            })
            
            # Mark image position in HTML
            marker = soup.new_tag('span')
            marker.string = f'[IMAGE_{len(images_with_context) - 1}_HERE]'
            img.replace_with(marker)
        
        # Step 2: Convert clean text to markdown
        h2t = html2text.HTML2Text()
        h2t.body_width = 0
        h2t.ignore_links = False
        h2t.ignore_images = True  # We handle images separately
        h2t.ignore_tables = True  # Ignore tables for clean text
        
        markdown = h2t.handle(str(soup))
        
        # Step 3: Insert images at marked positions
        for i, img_data in enumerate(images_with_context):
            marker = f'[IMAGE_{i}_HERE]'
            img_markdown = f"\n\n![{img_data['alt']}]({img_data['src']})\n\n"
            markdown = markdown.replace(marker, img_markdown)
        
        # Clean up
        markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)
        markdown = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF]+', '', markdown)
        
        return markdown.strip()


def convert_with_images(html_content: str, approach: str = 'preserve_tables') -> str:
    """
    Convert HTML to markdown with images
    
    Args:
        html_content: HTML to convert
        approach: 'preserve_tables' (keep structure) or 'hybrid' (extract and merge)
    
    Returns:
        Markdown with images
    """
    if approach == 'hybrid':
        converter = HybridConverter()
        return converter.convert(html_content)
    else:
        converter = ImagePreservingConverter()
        return converter.convert(html_content)