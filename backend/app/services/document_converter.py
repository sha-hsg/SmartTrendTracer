"""
Enhanced Document Converter Service
Uses best-in-class libraries for document conversion
"""
import os
import re
import tempfile
from typing import Optional, List, Dict, Any
from pathlib import Path
import subprocess
import shutil
import asyncio

# Try Playwright for browser-based conversion (best for complex HTML with images)
try:
    from app.services.playwright_converter import PlaywrightConverter, convert_html_to_markdown_sync
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not available, falling back to other converters")

# Try Trafilatura for article extraction (best for cleaning HTML)
try:
    from trafilatura import extract
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False

# Try MarkItDown as secondary converter (Microsoft's solution)
try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False

# Try pypandoc as converter (best quality markdown output)
try:
    import pypandoc
    PYPANDOC_AVAILABLE = True
    # Check if pandoc binary is installed
    try:
        pypandoc.get_pandoc_version()
    except:
        PYPANDOC_AVAILABLE = False
except ImportError:
    PYPANDOC_AVAILABLE = False

# Use markdownify as tertiary converter
try:
    import markdownify
    MARKDOWNIFY_AVAILABLE = True
except ImportError:
    MARKDOWNIFY_AVAILABLE = False

# Try html-to-markdown as quaternary option
try:
    from html_to_markdown import convert_to_markdown
    HTML_TO_MARKDOWN_AVAILABLE = True
except ImportError:
    HTML_TO_MARKDOWN_AVAILABLE = False

# Import html2text as fallback (always import for error handling)
try:
    import html2text
    HTML2TEXT_AVAILABLE = True
except ImportError:
    HTML2TEXT_AVAILABLE = False

# Markdown processing
import mistune
from markdown_it import MarkdownIt
try:
    from mdit_py_plugins.footnote import footnote_plugin
    from mdit_py_plugins.tasklists import tasklists_plugin
    MARKDOWN_IT_PLUGINS = True
except ImportError:
    MARKDOWN_IT_PLUGINS = False

# PDF generation
try:
    import pypandoc
    PANDOC_AVAILABLE = True
except ImportError:
    PANDOC_AVAILABLE = False

try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

try:
    from md2pdf.core import md2pdf
    MD2PDF_AVAILABLE = True
except ImportError:
    MD2PDF_AVAILABLE = False


class DocumentConverter:
    """
    Unified document converter using best available libraries
    """
    
    def __init__(self):
        """Initialize converter with best available libraries"""
        # Use Playwright as primary for complex HTML with images
        self.use_playwright = PLAYWRIGHT_AVAILABLE
        # Use Trafilatura + pypandoc as secondary combo
        self.use_trafilatura = TRAFILATURA_AVAILABLE and PYPANDOC_AVAILABLE and not self.use_playwright
        # Fallback options if primary converters not available
        self.use_markitdown = MARKITDOWN_AVAILABLE and not self.use_trafilatura and not self.use_playwright
        self.use_pypandoc_alone = PYPANDOC_AVAILABLE and not self.use_trafilatura and not MARKITDOWN_AVAILABLE and not self.use_playwright
        self.use_markdownify = MARKDOWNIFY_AVAILABLE and not self.use_trafilatura and not MARKITDOWN_AVAILABLE and not self.use_pypandoc_alone and not self.use_playwright
        self.use_html_to_markdown = HTML_TO_MARKDOWN_AVAILABLE and not self.use_trafilatura and not MARKITDOWN_AVAILABLE and not self.use_pypandoc_alone and not MARKDOWNIFY_AVAILABLE and not self.use_playwright
        
        # Initialize MarkItDown if available
        if self.use_markitdown:
            self.markitdown = MarkItDown()
        
        if not self.use_trafilatura and not self.use_markitdown and not self.use_pypandoc_alone and not self.use_markdownify and not self.use_html_to_markdown:
            # Setup html2text converter as fallback
            if HTML2TEXT_AVAILABLE:
                self.h2t = html2text.HTML2Text()
                self.h2t.body_width = 0  # Don't wrap lines
                self.h2t.ignore_links = False
                self.h2t.ignore_images = False
                self.h2t.images_to_alt = False
                self.h2t.include_link_brackets = False
                self.h2t.mark_code = True
                self.h2t.wrap_links = False
                self.h2t.wrap_list_items = False
        
        # Setup html2text for fallback scenarios even if using other converters
        if HTML2TEXT_AVAILABLE:
            self.h2t = html2text.HTML2Text()
            self.h2t.body_width = 0
            self.h2t.ignore_links = False
            self.h2t.ignore_images = False
        
        converter_name = ('Playwright (browser-based)' if self.use_playwright else
                         'trafilatura+pypandoc' if self.use_trafilatura else
                         'markitdown' if self.use_markitdown else
                         'pypandoc' if self.use_pypandoc_alone else 
                         'markdownify' if self.use_markdownify else 
                         'html-to-markdown' if self.use_html_to_markdown else 
                         'html2text')
        print(f"Using HTML to Markdown converter: {converter_name}")
        
        # Setup markdown parser
        self.md_parser = MarkdownIt("commonmark").enable(["table", "strikethrough"])
        if MARKDOWN_IT_PLUGINS:
            self.md_parser.use(footnote_plugin)
            self.md_parser.use(tasklists_plugin)
        
        # Check which PDF libraries are available
        self.pdf_method = self._determine_pdf_method()
        print(f"PDF conversion method: {self.pdf_method}")
    
    def _determine_pdf_method(self) -> str:
        """Determine the best available PDF conversion method"""
        if PANDOC_AVAILABLE:
            # Check if pandoc is installed
            if shutil.which('pandoc'):
                return 'pandoc'
        
        if WEASYPRINT_AVAILABLE:
            return 'weasyprint'
        
        if MD2PDF_AVAILABLE:
            return 'md2pdf'
        
        return 'reportlab'  # Fallback to existing ReportLab implementation
    
    def _extract_media_urls(self, html_content: str) -> List[Dict[str, str]]:
        """Extract iframe and video URLs from HTML for preservation"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        media_items = []
        
        # Extract iframes (YouTube, Vimeo, etc.)
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src:
                # Clean up YouTube embed URLs to watch URLs
                if 'youtube.com/embed/' in src:
                    video_id = src.split('/embed/')[1].split('?')[0]
                    clean_url = f'https://www.youtube.com/watch?v={video_id}'
                    media_items.append({'type': 'video', 'url': clean_url, 'original': src})
                elif 'vimeo.com/video/' in src:
                    video_id = src.split('/video/')[1].split('?')[0]
                    clean_url = f'https://vimeo.com/{video_id}'
                    media_items.append({'type': 'video', 'url': clean_url, 'original': src})
                else:
                    media_items.append({'type': 'iframe', 'url': src, 'original': src})
        
        # Extract video tags
        for video in soup.find_all('video'):
            src = video.get('src')
            if src:
                media_items.append({'type': 'video', 'url': src, 'original': src})
            # Check for source tags within video
            for source in video.find_all('source'):
                src = source.get('src')
                if src:
                    media_items.append({'type': 'video', 'url': src, 'original': src})
        
        # Extract Twitter/X embeds
        for blockquote in soup.find_all('blockquote', class_='twitter-tweet'):
            links = blockquote.find_all('a')
            for link in links:
                href = link.get('href')
                if href and 'twitter.com' in href or 'x.com' in href:
                    media_items.append({'type': 'tweet', 'url': href, 'original': href})
                    break
        
        return media_items
    
    def _preprocess_html_for_media(self, html_content: str) -> str:
        """Preprocess HTML to convert media elements to placeholder links before extraction"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # First, extract content from layout tables (Substack uses tables for layout)
        # This is critical to avoid markdown table artifacts
        for table in soup.find_all('table'):
            # Check if this is a layout table (no actual data)
            # Layout tables typically have one column or are used for formatting
            rows = table.find_all('tr')
            is_layout_table = True
            
            # Check if this looks like a data table
            # Data tables usually have multiple columns with consistent structure
            if rows:
                cells_per_row = [len(row.find_all(['td', 'th'])) for row in rows]
                # If all rows have more than 2 cells and consistent count, might be data table
                if cells_per_row and max(cells_per_row) > 2 and len(set(cells_per_row)) <= 2:
                    # Check if cells contain mostly text (not nested structures)
                    first_row_cells = rows[0].find_all(['td', 'th'])
                    text_cells = sum(1 for cell in first_row_cells if cell.get_text(strip=True) and not cell.find_all(['div', 'table', 'p']))
                    if text_cells > len(first_row_cells) / 2:
                        is_layout_table = False
            
            if is_layout_table:
                # Extract all content from the table and replace it
                # We need to be careful to preserve img tags properly
                new_content = []
                
                # First pass: collect all meaningful content elements
                for element in table.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'ul', 'ol', 'pre', 'code']):
                    new_content.append(element.extract())
                
                # Second pass: collect images separately to preserve their attributes
                for img in table.find_all('img'):
                    # Create a new img tag with preserved attributes
                    new_img = soup.new_tag('img')
                    # Copy all attributes
                    for attr, value in img.attrs.items():
                        new_img[attr] = value
                    # Wrap in a paragraph for better markdown conversion
                    p = soup.new_tag('p')
                    p.append(new_img)
                    new_content.append(p)
                
                # Third pass: collect links that aren't part of other elements
                for link in table.find_all('a'):
                    # Check if this link is standalone (not inside a p, h1, etc)
                    if link.parent.name in ['td', 'th']:
                        new_content.append(link.extract())
                
                # Fourth pass: extract remaining text content from cells
                for cell in table.find_all(['td', 'th']):
                    # Get direct text content that hasn't been extracted
                    text = cell.get_text(strip=True)
                    if text and len(text) > 1:  # Skip empty or single char cells
                        # Check if this text is substantial and not already extracted
                        if not any(text in str(content) for content in new_content):
                            p = soup.new_tag('p')
                            p.string = text
                            new_content.append(p)
                
                # Replace the table with its content
                for content in reversed(new_content):
                    table.insert_after(content)
                table.decompose()
        
        # Convert iframes to markdown links
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if src:
                # Create a descriptive link based on the source
                if 'youtube.com/embed/' in src:
                    video_id = src.split('/embed/')[1].split('?')[0]
                    clean_url = f'https://www.youtube.com/watch?v={video_id}'
                    link_text = f'[📹 Watch on YouTube]({clean_url})'
                elif 'vimeo.com/video/' in src:
                    video_id = src.split('/video/')[1].split('?')[0]
                    clean_url = f'https://vimeo.com/{video_id}'
                    link_text = f'[📹 Watch on Vimeo]({clean_url})'
                elif 'twitter.com' in src or 'x.com' in src:
                    link_text = f'[🐦 View Tweet]({src})'
                else:
                    # Generic iframe
                    link_text = f'[🔗 View Embedded Content]({src})'
                
                # Create a paragraph element with the link
                p = soup.new_tag('p')
                p.string = link_text
                iframe.replace_with(p)
        
        # Convert video tags to markdown links
        for video in soup.find_all('video'):
            src = video.get('src')
            if not src:
                # Check for source tags within video
                source = video.find('source')
                if source:
                    src = source.get('src')
            
            if src:
                p = soup.new_tag('p')
                p.string = f'[📹 Video]({src})'
                video.replace_with(p)
        
        # Convert Twitter blockquotes to links
        for blockquote in soup.find_all('blockquote', class_='twitter-tweet'):
            # Find the tweet link within the blockquote
            tweet_link = None
            for link in blockquote.find_all('a'):
                href = link.get('href', '')
                if 'twitter.com' in href or 'x.com' in href:
                    tweet_link = href
                    break
            
            if tweet_link:
                p = soup.new_tag('p')
                p.string = f'[🐦 View Tweet]({tweet_link})'
                blockquote.replace_with(p)
        
        # Handle audio tags
        for audio in soup.find_all('audio'):
            src = audio.get('src')
            if not src:
                source = audio.find('source')
                if source:
                    src = source.get('src')
            
            if src:
                p = soup.new_tag('p')
                p.string = f'[🎵 Audio]({src})'
                audio.replace_with(p)
        
        # Ensure images have proper alt text and are preserved
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            width = img.get('width', '')
            height = img.get('height', '')
            
            # Skip tracking pixels and tiny images
            # Check for 1x1 images or tracking URLs
            if (width == '1' and height == '1') or any(x in src.lower() for x in ['eotrx', 'open?token', 'track', 'analytics', 'pixel']):
                img.decompose()
                continue
            
            # Skip small UI icons (18x18 are typically UI elements in Substack)
            if width == '18' and height == '18':
                img.decompose()
                continue
            
            # Skip profile pictures and small avatars (40x40)
            if width == '40' and height == '40':
                img.decompose()
                continue
                
            # Ensure the image has alt text
            if not alt:
                # Try to extract meaningful alt from src
                if 'substack' in src.lower():
                    alt = 'Article image'
                else:
                    alt = 'Image'
            img['alt'] = alt
        
        return str(soup)
    
    def _convert_with_trafilatura(self, html_content: str) -> str:
        """Convert HTML to clean markdown using Trafilatura for best article extraction"""
        from bs4 import BeautifulSoup
        
        # First clean the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove tracking and UI elements
        for element in soup.find_all(['script', 'style', 'meta', 'link', 'noscript']):
            element.decompose()
        
        # Note which images should be preserved (for future reference)
        content_images = []
        for img in soup.find_all('img'):
            width = img.get('width', '')
            height = img.get('height', '')
            src = img.get('src', '')
            
            # Skip tracking pixels and UI icons
            if (str(width) in ['1', '18', '40'] or str(height) in ['1', '18', '40'] or
                any(x in src.lower() for x in ['eotrx', 'open?token', 'track', 'analytics', 'pixel'])):
                img.decompose()
            else:
                # This is a content image - note it for future enhancements
                content_images.append({
                    'src': src,
                    'alt': img.get('alt', 'Article image')
                })
        
        # Use Trafilatura for clean extraction
        try:
            article_text = extract(
                str(soup),
                output_format='markdown',
                include_links=True,
                include_formatting=True,
                include_images=False,  # Images don't work well with Substack HTML structure
                target_language='en',
                favor_precision=True
            )
            
            if article_text:
                markdown_text = article_text
            else:
                # Fallback to basic extraction
                markdown_text = soup.get_text(separator='\n\n')
        except Exception as e:
            print(f"Trafilatura failed: {e}")
            # Fallback to text extraction
            markdown_text = soup.get_text(separator='\n\n')
        
        # Post-process to clean up
        markdown_text = self._postprocess_markdown(markdown_text)
        
        # Add a note about images if any were found
        if content_images:
            note = f"\n\n*Note: This article originally contained {len(content_images)} images which are viewable in the original article.*\n"
            markdown_text += note
        
        return markdown_text
    
    def _postprocess_markdown(self, markdown_text: str) -> str:
        """Post-process markdown to clean up conversion artifacts"""
        import re
        
        # Remove markdown table artifacts from layout tables
        # Look for patterns like | --- | --- | or |  |  | with empty or minimal content
        lines = markdown_text.split('\n')
        cleaned_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip table separator lines
            if re.match(r'^\s*\|[\s\-\|]+\|\s*$', line):
                # Check if this is part of a layout table (not a data table)
                # Look ahead and behind for context
                is_layout_table = True
                
                # Check previous lines for table content
                if i > 0 and '|' in lines[i-1]:
                    # Count cells in previous line
                    cells = [c.strip() for c in lines[i-1].split('|') if c.strip()]
                    # If cells have substantial content, might be a data table
                    if cells and any(len(cell) > 10 for cell in cells):
                        is_layout_table = False
                
                if is_layout_table:
                    # Skip this separator line
                    i += 1
                    continue
            
            # Remove empty table rows like |  |  |
            if re.match(r'^\s*\|[\s\|]*\|\s*$', line):
                i += 1
                continue
            
            # Clean up single-cell table rows (common in Substack layout)
            # Pattern: | content | -> content
            if re.match(r'^\s*\|\s*([^|]+)\s*\|\s*$', line):
                match = re.match(r'^\s*\|\s*([^|]+)\s*\|\s*$', line)
                content = match.group(1).strip()
                if content:
                    cleaned_lines.append(content)
                i += 1
                continue
            
            # Clean up rows with mostly empty cells
            if '|' in line:
                cells = line.split('|')
                non_empty_cells = [c.strip() for c in cells if c.strip()]
                # If only one cell has content, extract it
                if len(non_empty_cells) == 1:
                    cleaned_lines.append(non_empty_cells[0])
                    i += 1
                    continue
                # If most cells are empty, it's probably layout
                elif len(non_empty_cells) < len(cells) / 3:
                    # Extract any meaningful content
                    for cell in non_empty_cells:
                        if cell and not cell == '---':
                            cleaned_lines.append(cell)
                    i += 1
                    continue
            
            # Keep the line as is
            cleaned_lines.append(line)
            i += 1
        
        markdown_text = '\n'.join(cleaned_lines)
        
        # Fix markdown links that might have been broken
        # Convert [text](url) patterns that might have extra spaces
        markdown_text = re.sub(r'\[([^\]]+)\]\s+\(([^\)]+)\)', r'[\1](\2)', markdown_text)
        
        # Fix escaped square brackets in links (common pypandoc issue)
        markdown_text = markdown_text.replace(r'\[', '[')
        markdown_text = markdown_text.replace(r'\]', ']')
        
        # Ensure video/tweet links are properly formatted
        # Sometimes pypandoc escapes characters, fix that
        markdown_text = markdown_text.replace('\\📹', '📹')
        markdown_text = markdown_text.replace('\\🐦', '🐦')
        markdown_text = markdown_text.replace('\\🔗', '🔗')
        markdown_text = markdown_text.replace('\\🎵', '🎵')
        
        # Clean up excessive newlines
        markdown_text = re.sub(r'\n{4,}', '\n\n\n', markdown_text)
        
        # Remove any remaining empty table structures
        markdown_text = re.sub(r'\n\s*\|\s*\|\s*\n', '\n', markdown_text)
        
        return markdown_text

    def html_to_markdown(self, html_content: str, 
                         base_url: Optional[str] = None,
                         preserve_images: bool = True) -> str:
        """
        Convert HTML to clean Markdown using best available library
        
        Args:
            html_content: HTML string to convert
            base_url: Base URL for relative links
            preserve_images: Whether to preserve image tags
        
        Returns:
            Clean markdown string
        """
        if not html_content:
            return ""
        
        if self.use_playwright:
            # Use browser-based conversion for best results with images
            try:
                markdown_text = convert_html_to_markdown_sync(html_content, base_url)
            except Exception as e:
                print(f"Error with Playwright converter: {e}, falling back to Trafilatura")
                # Fallback to next best converter
                if self.use_trafilatura:
                    try:
                        markdown_text = self._convert_with_trafilatura(html_content)
                    except Exception as e2:
                        print(f"Trafilatura also failed: {e2}")
                        markdown_text = self._convert_with_html2text(html_content, base_url)
                else:
                    markdown_text = self._convert_with_html2text(html_content, base_url)
        elif self.use_trafilatura:
            # Use Trafilatura + pypandoc combo for best results
            try:
                markdown_text = self._convert_with_trafilatura(html_content)
            except Exception as e:
                print(f"Error with Trafilatura+pypandoc, trying fallback: {e}")
                # Fallback to MarkItDown or other converters
                if self.use_markitdown:
                    try:
                        # Use MarkItDown fallback
                        import tempfile
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                            tmp.write(html_content)
                            tmp_path = tmp.name
                        try:
                            result = self.markitdown.convert(tmp_path)
                            markdown_text = result.text_content
                        finally:
                            os.unlink(tmp_path)
                    except Exception as e2:
                        print(f"MarkItDown also failed: {e2}")
                        markdown_text = self._convert_with_html2text(html_content, base_url)
                else:
                    markdown_text = self._convert_with_html2text(html_content, base_url)
        elif self.use_markitdown:
            # Use MarkItDown as primary converter
            try:
                # MarkItDown expects text content, not file path
                # We create a temporary file to use with MarkItDown
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                    tmp.write(html_content)
                    tmp_path = tmp.name
                
                try:
                    # Convert using MarkItDown
                    result = self.markitdown.convert(tmp_path)
                    markdown_text = result.text_content
                finally:
                    # Clean up temp file
                    os.unlink(tmp_path)
                    
            except Exception as e:
                print(f"Error with MarkItDown, trying pypandoc: {e}")
                # Fallback to pypandoc
                if PYPANDOC_AVAILABLE:
                    try:
                        markdown_text = self._convert_with_pypandoc(html_content)
                    except Exception as e2:
                        print(f"Error with pypandoc, trying markdownify: {e2}")
                        if MARKDOWNIFY_AVAILABLE:
                            try:
                                markdown_text = self._convert_with_markdownify(html_content)
                            except Exception as e3:
                                print(f"Error with markdownify, falling back to html2text: {e3}")
                                markdown_text = self._convert_with_html2text(html_content, base_url)
                        else:
                            markdown_text = self._convert_with_html2text(html_content, base_url)
                elif MARKDOWNIFY_AVAILABLE:
                    try:
                        markdown_text = self._convert_with_markdownify(html_content)
                    except Exception as e2:
                        print(f"Error with markdownify, falling back to html2text: {e2}")
                        markdown_text = self._convert_with_html2text(html_content, base_url)
                else:
                    markdown_text = self._convert_with_html2text(html_content, base_url)
        elif self.use_markdownify:
            # Use markdownify as primary converter
            try:
                markdown_text = self._convert_with_markdownify(html_content)
            except Exception as e:
                print(f"Error with markdownify, trying pypandoc: {e}")
                # Fallback to pypandoc
                if self.use_pypandoc:
                    try:
                        markdown_text = self._convert_with_pypandoc(html_content)
                    except Exception as e2:
                        print(f"Error with pypandoc, falling back to html2text: {e2}")
                        markdown_text = self._convert_with_html2text(html_content, base_url)
                else:
                    markdown_text = self._convert_with_html2text(html_content, base_url)
        elif self.use_pypandoc:
            # Use pypandoc as primary converter - highest quality conversion
            try:
                # First clean the HTML
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove script and style tags
                for tag in soup(['script', 'style', 'meta', 'link', 'noscript']):
                    tag.decompose()
                
                # Get cleaned HTML
                cleaned_html = str(soup)
                
                # Use pypandoc to convert
                extra_args = [
                    '--wrap=none',  # Don't wrap lines
                    '--markdown-headings=atx',  # Use # style headings
                    '--no-highlight',  # Don't highlight code
                ]
                
                markdown_text = pypandoc.convert_text(
                    cleaned_html,
                    'markdown',  # Standard markdown format
                    format='html',  # Source format
                    extra_args=extra_args
                )
            except Exception as e:
                print(f"Error with pypandoc, trying markdownify: {e}")
                # Fallback to markdownify
                if self.use_markdownify:
                    try:
                        markdown_text = self._convert_with_markdownify(html_content)
                    except Exception as e2:
                        print(f"Error with markdownify, falling back to html2text: {e2}")
                        markdown_text = self._convert_with_html2text(html_content, base_url)
                else:
                    markdown_text = self._convert_with_html2text(html_content, base_url)
        elif self.use_markdownify:
            # Use markdownify as secondary converter
            try:
                markdown_text = self._convert_with_markdownify(html_content)
            except Exception as e:
                print(f"Error with markdownify, trying html-to-markdown: {e}")
                # Try html-to-markdown next
                if self.use_html_to_markdown:
                    try:
                        options = {
                            'strip': ['script', 'style'],
                            'autolinks': True,
                            'heading_style': 'atx',
                            'code_language': '',
                            'escape_asterisks': False,
                            'escape_underscores': False,
                            'escape_misc': False,
                            'highlight_style': 'bold',
                            'strong_em_symbol': '*',
                            'convert_as_inline': False,
                            'strip_newlines': False,
                            'wrap': False,
                            'preprocess_html': True,
                            'preprocessing_preset': 'standard',
                            'remove_navigation': True,
                            'remove_forms': True,
                        }
                        markdown_text = convert_to_markdown(html_content, **options)
                    except Exception as e2:
                        print(f"Error with html-to-markdown, falling back to html2text: {e2}")
                        # Final fallback to html2text
                        if not hasattr(self, 'h2t'):
                            self.h2t = html2text.HTML2Text()
                            self.h2t.body_width = 0
                        if base_url:
                            self.h2t.baseurl = base_url
                        markdown_text = self.h2t.handle(html_content)
                else:
                    # Fallback to html2text
                    if not hasattr(self, 'h2t'):
                        self.h2t = html2text.HTML2Text()
                        self.h2t.body_width = 0
                    if base_url:
                        self.h2t.baseurl = base_url
                    markdown_text = self.h2t.handle(html_content)
        elif self.use_html_to_markdown:
            # Use html-to-markdown library
            try:
                # Configure options for html-to-markdown
                options = {
                    'strip': ['script', 'style'],  # Remove script and style tags
                    'autolinks': True,  # Convert URLs to links
                    'heading_style': 'atx',  # Use # style headings
                    'code_language': '',  # Don't add language to code blocks by default
                    'escape_asterisks': False,  # Don't escape asterisks
                    'escape_underscores': False,  # Don't escape underscores
                    'escape_misc': False,  # Don't escape other characters
                    'highlight_style': 'bold',  # Use bold for highlights
                    'strong_em_symbol': '*',  # Use * for bold/emphasis
                    'convert_as_inline': False,  # Keep block structure
                    'strip_newlines': False,  # Preserve newlines
                    'wrap': False,  # Don't wrap lines
                    'preprocess_html': True,  # Clean up HTML before conversion
                    'preprocessing_preset': 'standard',  # Standard preprocessing
                    'remove_navigation': True,  # Remove navigation elements
                    'remove_forms': True,  # Remove form elements
                }
                
                markdown_text = convert_to_markdown(html_content, **options)
            except Exception as e:
                print(f"Error with html-to-markdown, falling back to html2text: {e}")
                # Fallback to html2text if there's an error
                if not hasattr(self, 'h2t'):
                    self.h2t = html2text.HTML2Text()
                    self.h2t.body_width = 0
                if base_url:
                    self.h2t.baseurl = base_url
                markdown_text = self.h2t.handle(html_content)
        else:
            # Use html2text as fallback
            if base_url:
                self.h2t.baseurl = base_url
            markdown_text = self.h2t.handle(html_content)
        
        # Clean up common artifacts
        markdown_text = self._clean_markdown(markdown_text)
        
        return markdown_text
    
    def _clean_markdown(self, markdown_text: str) -> str:
        """Clean up markdown text from common conversion artifacts"""
        # Remove excessive blank lines
        markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
        
        # Fix broken markdown links
        markdown_text = re.sub(r'\[([^\]]+)\]\s+\(([^\)]+)\)', r'[\1](\2)', markdown_text)
        
        # Remove tracking pixels and 1x1 images
        markdown_text = re.sub(
            r'!\[[^\]]*\]\([^)]*(?:pixel|track|1x1|spacer)[^)]*\)',
            '', 
            markdown_text, 
            flags=re.IGNORECASE
        )
        
        # Clean up empty headings
        markdown_text = re.sub(r'^#+\s*$', '', markdown_text, flags=re.MULTILINE)
        
        # Remove Substack-specific footer patterns
        footer_patterns = [
            r'©\s*\d{4}.*?(?:\n|$)',
            r'Start writing on Substack.*?(?:\n|$)',
            r'Get the app.*?(?:\n|$)',
            r'Unsubscribe.*?(?:\n|$)',
            r'\[Share\]\s*\[Subscribe\].*?(?:\n|$)',
        ]
        
        for pattern in footer_patterns:
            markdown_text = re.sub(pattern, '', markdown_text, flags=re.IGNORECASE | re.DOTALL)
        
        return markdown_text.strip()
    
    def _convert_with_pypandoc(self, html_content: str) -> str:
        """Helper method to convert HTML using pypandoc"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style tags
        for tag in soup(['script', 'style', 'meta', 'link', 'noscript']):
            tag.decompose()
        
        # Get cleaned HTML
        cleaned_html = str(soup)
        
        # Use pypandoc to convert
        extra_args = [
            '--wrap=none',  # Don't wrap lines
            '--markdown-headings=atx',  # Use # style headings
            '--no-highlight',  # Don't highlight code
        ]
        
        markdown_text = pypandoc.convert_text(
            cleaned_html,
            'markdown',  # Standard markdown format
            format='html',  # Source format
            extra_args=extra_args
        )
        return markdown_text
    
    def _convert_with_markdownify(self, html_content: str) -> str:
        """Helper method to convert HTML using markdownify"""
        # Configure options for markdownify
        # Note: markdownify doesn't support both 'strip' and 'convert' at the same time
        # We use strip to remove unwanted tags
        return markdownify.markdownify(
            html_content,
            heading_style="ATX",  # Use # style headings
            bullets="*-+",  # Bullet characters for lists
            strong_em_symbol="*",  # Use * for bold/emphasis
            strip=['script', 'style', 'meta', 'link', 'noscript', 'head', 'header', 'footer', 'nav', 'aside'],  # Remove these tags
            wrap=False,  # Don't wrap lines
            wrap_width=0,  # No line wrapping
            keep_inline_images_in=['p', 'div', 'li', 'td'],  # Keep images inline in these
            escape_asterisks=False,  # Don't escape asterisks
            escape_underscores=False,  # Don't escape underscores
            escape_misc=False,  # Don't escape other markdown chars
            default_title=True,  # Use default title for links without text
            exclude_styles=True,  # Exclude style attributes
        )
    
    def _convert_with_html2text(self, html_content: str, base_url: Optional[str] = None) -> str:
        """Helper method to convert HTML using html2text"""
        if not hasattr(self, 'h2t'):
            self.h2t = html2text.HTML2Text()
            self.h2t.body_width = 0
            self.h2t.ignore_links = False
            self.h2t.ignore_images = False
        if base_url:
            self.h2t.baseurl = base_url
        return self.h2t.handle(html_content)
    
    def markdown_to_pdf_pandoc(self, markdown_text: str, 
                               output_path: Optional[str] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Convert Markdown to PDF using Pandoc (best quality)
        
        Args:
            markdown_text: Markdown content
            output_path: Optional path to save PDF
            metadata: Document metadata (title, author, date)
        
        Returns:
            PDF bytes
        """
        # Prepare metadata
        pandoc_args = [
            '--pdf-engine=xelatex',  # Better Unicode support
            '--template=eisvogel',  # Professional template (if installed)
            '--listings',  # Code highlighting
            '--toc',  # Table of contents
            '--toc-depth=3',
            '--highlight-style=tango',
        ]
        
        # Add metadata
        if metadata:
            if 'title' in metadata:
                pandoc_args.extend(['-M', f'title={metadata["title"]}'])
            if 'author' in metadata:
                pandoc_args.extend(['-M', f'author={metadata["author"]}'])
            if 'date' in metadata:
                pandoc_args.extend(['-M', f'date={metadata["date"]}'])
        
        # Convert
        if output_path:
            pypandoc.convert_text(
                markdown_text,
                'pdf',
                format='markdown',
                outputfile=output_path,
                extra_args=pandoc_args
            )
            with open(output_path, 'rb') as f:
                return f.read()
        else:
            return pypandoc.convert_text(
                markdown_text,
                'pdf',
                format='markdown',
                extra_args=pandoc_args
            ).encode('latin-1')
    
    def markdown_to_pdf_weasyprint(self, markdown_text: str,
                                   css_style: Optional[str] = None) -> bytes:
        """
        Convert Markdown to PDF using WeasyPrint (good CSS support)
        
        Args:
            markdown_text: Markdown content
            css_style: Optional CSS styling
        
        Returns:
            PDF bytes
        """
        # First convert markdown to HTML
        html_content = mistune.html(markdown_text)
        
        # Add CSS styling
        if not css_style:
            css_style = """
            @page {
                size: A4;
                margin: 2.5cm;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            h1, h2, h3 {
                color: #2c3e50;
                margin-top: 1.5em;
            }
            h1 { font-size: 24pt; }
            h2 { font-size: 18pt; }
            h3 { font-size: 14pt; }
            p { margin-bottom: 1em; }
            code {
                background: #f4f4f4;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
            pre {
                background: #f4f4f4;
                padding: 1em;
                border-radius: 5px;
                overflow-x: auto;
            }
            blockquote {
                border-left: 4px solid #3498db;
                padding-left: 1em;
                margin-left: 0;
                color: #666;
                font-style: italic;
            }
            img {
                max-width: 100%;
                height: auto;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f4f4f4;
                font-weight: bold;
            }
            """
        
        # Create full HTML document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>{css_style}</style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Convert to PDF
        pdf_file = weasyprint.HTML(string=full_html).write_pdf()
        return pdf_file
    
    def markdown_to_pdf_md2pdf(self, markdown_text: str,
                               output_path: str,
                               css_file_path: Optional[str] = None) -> bytes:
        """
        Convert Markdown to PDF using md2pdf (simple and effective)
        
        Args:
            markdown_text: Markdown content
            output_path: Path to save PDF
            css_file_path: Optional CSS file path
        
        Returns:
            PDF bytes
        """
        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write(markdown_text)
            tmp_path = tmp.name
        
        try:
            # Convert to PDF
            md2pdf(
                pdf_file_path=output_path,
                md_content=markdown_text,
                css_file_path=css_file_path,
                base_url=os.path.dirname(tmp_path)
            )
            
            # Read and return PDF
            with open(output_path, 'rb') as f:
                return f.read()
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
    
    def markdown_to_pdf(self, markdown_text: str,
                       output_path: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None,
                       css_style: Optional[str] = None) -> bytes:
        """
        Convert Markdown to PDF using the best available method
        
        Args:
            markdown_text: Markdown content
            output_path: Optional path to save PDF
            metadata: Document metadata
            css_style: Optional CSS styling
        
        Returns:
            PDF bytes
        """
        if self.pdf_method == 'pandoc':
            return self.markdown_to_pdf_pandoc(markdown_text, output_path, metadata)
        elif self.pdf_method == 'weasyprint':
            pdf_bytes = self.markdown_to_pdf_weasyprint(markdown_text, css_style)
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
            return pdf_bytes
        elif self.pdf_method == 'md2pdf':
            if not output_path:
                output_path = tempfile.mktemp(suffix='.pdf')
            return self.markdown_to_pdf_md2pdf(markdown_text, output_path, css_style)
        else:
            # Fallback to existing ReportLab implementation
            from app.services.pdf_export_service import PDFExportService
            # This would need to be adapted to work with raw markdown
            raise NotImplementedError("ReportLab fallback needs implementation")
    
    def validate_markdown(self, markdown_text: str) -> List[str]:
        """
        Validate markdown syntax and return any issues
        
        Args:
            markdown_text: Markdown to validate
        
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        # Check for unclosed code blocks
        code_blocks = re.findall(r'```', markdown_text)
        if len(code_blocks) % 2 != 0:
            issues.append("Unclosed code block detected")
        
        # Check for broken links
        links = re.findall(r'\[([^\]]*)\]\(([^\)]*)\)', markdown_text)
        for text, url in links:
            if not url:
                issues.append(f"Empty URL in link: [{text}]()")
            elif url.startswith('#') and ' ' in url:
                issues.append(f"Space in anchor link: [{text}]({url})")
        
        # Check for broken images
        images = re.findall(r'!\[([^\]]*)\]\(([^\)]*)\)', markdown_text)
        for alt, url in images:
            if not url:
                issues.append(f"Empty URL in image: ![{alt}]()")
        
        return issues
    
    def extract_images_from_markdown(self, markdown_text: str) -> List[Dict[str, str]]:
        """
        Extract all image URLs and alt texts from markdown
        
        Args:
            markdown_text: Markdown content
        
        Returns:
            List of dicts with 'url' and 'alt' keys
        """
        images = []
        
        # Find markdown images
        md_images = re.findall(r'!\[([^\]]*)\]\(([^\)]+)\)', markdown_text)
        for alt, url in md_images:
            images.append({'alt': alt, 'url': url})
        
        # Find HTML images (in case they're embedded)
        html_images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']*)["\']', markdown_text)
        for url, alt in html_images:
            images.append({'alt': alt, 'url': url})
        
        return images


# Convenience functions for backward compatibility
def html_to_markdown(html_content: str, base_url: Optional[str] = None) -> str:
    """Convert HTML to Markdown using the best available method"""
    converter = DocumentConverter()
    return converter.html_to_markdown(html_content, base_url)


def markdown_to_pdf(markdown_text: str, output_path: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> bytes:
    """Convert Markdown to PDF using the best available method"""
    converter = DocumentConverter()
    return converter.markdown_to_pdf(markdown_text, output_path, metadata)