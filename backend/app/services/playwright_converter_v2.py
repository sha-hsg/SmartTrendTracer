"""
Optimized Playwright-based HTML to Markdown Converter for Substack
Focuses on extracting clean article content with images at correct positions
"""
import asyncio
import re
from typing import Dict, Optional, List
from playwright.async_api import async_playwright, Page
import logging

logger = logging.getLogger(__name__)


class PlaywrightSubstackConverter:
    """
    Specialized browser-based converter for Substack HTML content
    """
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the browser instance"""
        if not self._initialized:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            self._initialized = True
    
    async def close(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False
    
    async def convert_html_to_markdown(
        self, 
        html_content: str, 
        url: Optional[str] = None
    ) -> str:
        """
        Convert Substack HTML to clean markdown with images preserved
        """
        if not self._initialized:
            await self.initialize()
        
        page = await self.browser.new_page()
        
        try:
            # Load the HTML content
            await page.set_content(html_content, wait_until='domcontentloaded')
            
            # Extract and process content
            markdown = await page.evaluate("""
                () => {
                    // Find all images first and mark their positions
                    const images = [];
                    const contentImages = document.querySelectorAll('img');
                    
                    contentImages.forEach((img, index) => {
                        const width = parseInt(img.width) || parseInt(img.getAttribute('width')) || 0;
                        const height = parseInt(img.height) || parseInt(img.getAttribute('height')) || 0;
                        const src = img.src || img.getAttribute('src') || '';
                        
                        // Skip tracking pixels and icons
                        if (width > 50 && height > 50 && 
                            !src.includes('track') && 
                            !src.includes('pixel') && 
                            !src.includes('eotrx')) {
                            
                            // Create a unique placeholder
                            const placeholder = document.createElement('span');
                            placeholder.textContent = `[IMG_${index}]`;
                            placeholder.setAttribute('data-src', src);
                            placeholder.setAttribute('data-alt', img.alt || 'Image');
                            
                            // Replace image with placeholder
                            img.parentNode.replaceChild(placeholder, img);
                            
                            images.push({
                                id: index,
                                src: src,
                                alt: img.alt || 'Image'
                            });
                        } else {
                            // Remove tracking pixels
                            img.remove();
                        }
                    });
                    
                    // Extract the main content
                    let content = '';
                    
                    // Look for the main article content
                    const articleSelectors = [
                        '[role="article"]',
                        'article',
                        '.post-content',
                        '.email-content',
                        '[class*="body-markup"]',
                        'div.content'
                    ];
                    
                    let articleElement = null;
                    for (const selector of articleSelectors) {
                        articleElement = document.querySelector(selector);
                        if (articleElement) break;
                    }
                    
                    if (!articleElement) {
                        // Fallback: find the element with the most text content
                        const divs = Array.from(document.querySelectorAll('div'));
                        articleElement = divs.reduce((max, div) => 
                            (div.textContent || '').length > (max.textContent || '').length ? div : max
                        );
                    }
                    
                    // Convert to simple markdown
                    function elementToMarkdown(element) {
                        let markdown = '';
                        
                        for (const node of element.childNodes) {
                            if (node.nodeType === Node.TEXT_NODE) {
                                markdown += node.textContent;
                            } else if (node.nodeType === Node.ELEMENT_NODE) {
                                const tag = node.tagName.toLowerCase();
                                
                                switch(tag) {
                                    case 'h1':
                                        markdown += '\\n# ' + node.textContent + '\\n\\n';
                                        break;
                                    case 'h2':
                                        markdown += '\\n## ' + node.textContent + '\\n\\n';
                                        break;
                                    case 'h3':
                                        markdown += '\\n### ' + node.textContent + '\\n\\n';
                                        break;
                                    case 'h4':
                                        markdown += '\\n#### ' + node.textContent + '\\n\\n';
                                        break;
                                    case 'p':
                                        markdown += '\\n' + elementToMarkdown(node) + '\\n\\n';
                                        break;
                                    case 'strong':
                                    case 'b':
                                        markdown += '**' + node.textContent + '**';
                                        break;
                                    case 'em':
                                    case 'i':
                                        markdown += '*' + node.textContent + '*';
                                        break;
                                    case 'a':
                                        const href = node.getAttribute('href');
                                        if (href && !href.startsWith('javascript:')) {
                                            markdown += '[' + node.textContent + '](' + href + ')';
                                        } else {
                                            markdown += node.textContent;
                                        }
                                        break;
                                    case 'blockquote':
                                        const lines = elementToMarkdown(node).split('\\n');
                                        markdown += lines.map(line => line ? '> ' + line : '>').join('\\n') + '\\n\\n';
                                        break;
                                    case 'ul':
                                        for (const li of node.children) {
                                            markdown += '* ' + elementToMarkdown(li).trim() + '\\n';
                                        }
                                        markdown += '\\n';
                                        break;
                                    case 'ol':
                                        let i = 1;
                                        for (const li of node.children) {
                                            markdown += i + '. ' + elementToMarkdown(li).trim() + '\\n';
                                            i++;
                                        }
                                        markdown += '\\n';
                                        break;
                                    case 'code':
                                        markdown += '`' + node.textContent + '`';
                                        break;
                                    case 'pre':
                                        markdown += '\\n```\\n' + node.textContent + '\\n```\\n\\n';
                                        break;
                                    case 'span':
                                        // Check if it's our image placeholder
                                        if (node.textContent && node.textContent.startsWith('[IMG_')) {
                                            markdown += node.textContent;
                                        } else {
                                            markdown += elementToMarkdown(node);
                                        }
                                        break;
                                    case 'div':
                                        markdown += elementToMarkdown(node);
                                        break;
                                    case 'br':
                                        markdown += '\\n';
                                        break;
                                    default:
                                        markdown += elementToMarkdown(node);
                                }
                            }
                        }
                        
                        return markdown;
                    }
                    
                    content = elementToMarkdown(articleElement);
                    
                    // Replace image placeholders with markdown images
                    images.forEach(img => {
                        const placeholder = `[IMG_${img.id}]`;
                        const markdownImg = `![${img.alt}](${img.src})`;
                        content = content.replace(placeholder, markdownImg);
                    });
                    
                    return content;
                }
            """)
            
            # Clean up the markdown
            markdown = self._clean_markdown(markdown)
            
            return markdown
            
        except Exception as e:
            logger.error(f"Error converting HTML: {e}")
            # Fallback to simple text extraction
            return await page.evaluate("() => document.body.innerText")
            
        finally:
            await page.close()
    
    def _clean_markdown(self, markdown: str) -> str:
        """Clean up markdown artifacts"""
        # Fix escaped newlines
        markdown = markdown.replace('\\n', '\n')
        
        # Remove excessive newlines
        markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)
        
        # Remove empty headers
        markdown = re.sub(r'^#+\s*$', '', markdown, flags=re.MULTILINE)
        
        # Fix spacing around headers
        markdown = re.sub(r'(\n#+[^\n]+)\n(?!\n)', r'\1\n\n', markdown)
        
        # Remove tracking artifacts
        markdown = re.sub(r'͏|\u200B|\u200C|\u200D|\uFEFF', '', markdown)
        
        # Clean up whitespace
        markdown = re.sub(r'[ \t]+$', '', markdown, flags=re.MULTILINE)
        
        # Ensure single blank line between paragraphs
        markdown = re.sub(r'\n\n+(?=[^\n])', '\n\n', markdown)
        
        return markdown.strip()


# Convenience function for sync usage
def convert_substack_html_sync(html_content: str, url: Optional[str] = None) -> str:
    """Synchronous wrapper for the async converter"""
    async def _convert():
        converter = PlaywrightSubstackConverter()
        try:
            return await converter.convert_html_to_markdown(html_content, url)
        finally:
            await converter.close()
    
    return asyncio.run(_convert())