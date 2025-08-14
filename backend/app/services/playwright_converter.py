"""
Playwright-based HTML to Markdown Converter
Uses headless browser for perfect content extraction with images at correct positions
"""
import asyncio
import re
from typing import Dict, Optional, List
from playwright.async_api import async_playwright, Page
import logging

logger = logging.getLogger(__name__)


class PlaywrightConverter:
    """
    Browser-based HTML to Markdown converter that preserves images at correct positions
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
    ) -> Dict[str, any]:
        """
        Convert HTML to clean markdown with images preserved at correct positions
        
        Returns:
            Dict with 'markdown', 'images', and 'metadata'
        """
        if not self._initialized:
            await self.initialize()
        
        page = await self.browser.new_page()
        
        try:
            # Load the HTML content
            if url:
                await page.goto(url, wait_until='networkidle')
            else:
                await page.set_content(html_content, wait_until='networkidle')
            
            # Inject Readability.js for content extraction
            await page.add_script_tag(content=self._get_readability_script())
            
            # Extract article with images in correct positions
            article_data = await page.evaluate(self._get_extraction_script())
            
            # Convert to markdown with images
            markdown = self._convert_to_markdown(article_data)
            
            return {
                'markdown': markdown,
                'images': article_data.get('images', []),
                'title': article_data.get('title', ''),
                'author': article_data.get('byline', ''),
                'excerpt': article_data.get('excerpt', ''),
                'word_count': len(markdown.split())
            }
            
        except Exception as e:
            logger.error(f"Error converting HTML: {e}")
            # Fallback to basic extraction
            return self._fallback_extraction(html_content)
            
        finally:
            await page.close()
    
    def _get_readability_script(self) -> str:
        """Get Mozilla Readability.js library"""
        # Using a minified version of Readability.js
        # In production, you might want to load this from a file
        return """
        /*! Mozilla Readability - github.com/mozilla/readability */
        !function(t,e){"object"==typeof exports&&"undefined"!=typeof module?module.exports=e():"function"==typeof define&&define.amd?define(e):(t=t||self).Readability=e()}(this,function(){"use strict";function t(t,e){this._uri=t,this._doc=e,this._articleTitle=null,this._articleByline=null,this._articleDir=null,this._articleSiteName=null,this._attempts=[],this._debug=!1,this._maxElemsToParse=0,this._nbTopCandidates=5,this._charThreshold=500,this._classesToPreserve=[],this._keepClasses=!1,this._serializer=function(t){return t.innerHTML},this._flags=this.FLAG_STRIP_UNLIKELYS|this.FLAG_WEIGHT_CLASSES|this.FLAG_CLEAN_CONDITIONALLY,this._isProbablyReaderable=!1,this._isReadabilityDataTable=function(t){return t.readability};var i=function(t){for(;t&&"TABLE"!=t.tagName;)t=t.parentNode;return t};this._isDataTable=function(t){return"true"==t.getAttribute("datatable")?!0:"false"==t.getAttribute("datatable")?!1:t.getAttribute("summary")?!0:!!i(t)&&!!i(t).querySelector("caption")}}return t.prototype={FLAG_STRIP_UNLIKELYS:1,FLAG_WEIGHT_CLASSES:2,FLAG_CLEAN_CONDITIONALLY:4,ELEMENT_NODE:1,TEXT_NODE:3,DEFAULT_MAX_ELEMS_TO_PARSE:0,DEFAULT_N_TOP_CANDIDATES:5,DEFAULT_CHAR_THRESHOLD:500,REGEXPS:{unlikelyCandidates:/-ad-|ai2html|banner|breadcrumbs|combx|comment|community|cover-wrap|disqus|extra|footer|gdpr|header|legends|menu|related|remark|replies|rss|shoutbox|sidebar|skyscraper|social|sponsor|supplemental|ad-break|agegate|pagination|pager|popup|yom-remote/i,okMaybeItsACandidate:/and|article|body|column|content|main|shadow/i,positive:/article|body|content|entry|hentry|h-entry|main|page|pagination|post|text|blog|story/i,negative:/hidden|^hid$|hid$|hid |^hid |banner|combx|comment|com-|contact|foot|footer|footnote|gdpr|masthead|media|meta|outbrain|promo|related|scroll|share|shoutbox|sidebar|skyscraper|sponsor|shopping|tags|tool|widget/i,extraneous:/print|archive|comment|discuss|e[\-]?mail|share|reply|all|login|sign|single|utility/i,byline:/byline|author|dateline|writtenby|p-author/i,replaceFonts:/<(\/?)font[^>]*>/gi,normalize:/\s{2,}/g,videos:/\/\/(www\.)?((dailymotion|youtube|youtube-nocookie|player\.vimeo|v\.qq)\.com|(archive|upload\.wikimedia)\.org|player\.twitch\.tv)/i,shareElements:/(\b|_)(share|sharedaddy)(\b|_)/i,nextLink:/(next|weiter|continue|>([^\|]|$)|»([^\|]|$))/i,prevLink:/(prev|earl|old|new|<|«)/i,tokenize:/\W+/g,whitespace:/^\s*$/,hasContent:/\S$/,hashUrl:/^#.+/,srcsetUrl:/(\S+)(\s+[\d.]+[xw])?(\s*(?:,|$))/g,b64DataUrl:/^data:\s*([^\s;,]+)\s*;\s*base64\s*,/i},DIV_TO_P_ELEMS:new Set(["BLOCKQUOTE","DL","DIV","IMG","OL","P","PRE","TABLE","UL"]),ALTER_TO_DIV_EXCEPTIONS:["DIV","ARTICLE","SECTION","P"],PRESENTATIONAL_ATTRIBUTES:["align","background","bgcolor","border","cellpadding","cellspacing","frame","hspace","rules","style","valign","vspace","width"],DEPRECATED_SIZE_ATTRIBUTE_ELEMS:["TABLE","TH","TD","HR","PRE"],parse:function(){return this._isProbablyReaderable&&(this._debug=!0),this._debug&&console.log("**** Parsing document ****"),this._maxElemsToParse>0&&(this._debug&&console.log("Aborting parsing, reached max number of elements to parse"),{title:this._articleTitle||this._doc.title,byline:this._articleByline||"",dir:this._articleDir||"ltr",lang:"",content:"",textContent:"",length:0,excerpt:"",siteName:this._articleSiteName||""})}},t});
        """
    
    def _get_extraction_script(self) -> str:
        """JavaScript to extract content with image positions"""
        return """
        () => {
            // Clean up Substack-specific elements
            const elementsToRemove = [
                '.subscribe-widget',
                '.subscription-widget-wrap',
                '.email-header',
                '.email-footer',
                '[class*="forward"]',
                '[class*="outlook"]',
                '.gmail_quote'
            ];
            
            elementsToRemove.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => el.remove());
            });
            
            // Find all content images (not tracking pixels or icons)
            const contentImages = Array.from(document.querySelectorAll('img'))
                .filter(img => {
                    const width = parseInt(img.width) || parseInt(img.getAttribute('width')) || 0;
                    const height = parseInt(img.height) || parseInt(img.getAttribute('height')) || 0;
                    const src = img.src || img.getAttribute('src') || '';
                    
                    // Filter out tracking pixels and small UI elements
                    if (width <= 50 || height <= 50) return false;
                    if (src.includes('track') || src.includes('pixel') || src.includes('eotrx')) return false;
                    
                    return true;
                })
                .map((img, index) => {
                    // Find the paragraph or container this image belongs to
                    let container = img.closest('p, div, figure, article');
                    if (!container) container = img.parentElement;
                    
                    // Get surrounding text for context
                    const prevElement = container?.previousElementSibling;
                    const nextElement = container?.nextElementSibling;
                    
                    return {
                        src: img.src || img.getAttribute('src'),
                        alt: img.alt || img.getAttribute('alt') || 'Image',
                        index: index,
                        contextBefore: prevElement?.textContent?.slice(-200) || '',
                        contextAfter: nextElement?.textContent?.slice(0, 200) || '',
                        parentId: `IMG_PLACEHOLDER_${index}`
                    };
                });
            
            // Mark image positions in the DOM
            contentImages.forEach(imgData => {
                const img = document.querySelectorAll('img')[imgData.index];
                if (img) {
                    const placeholder = document.createElement('span');
                    placeholder.setAttribute('data-img-placeholder', imgData.parentId);
                    placeholder.textContent = `{{${imgData.parentId}}}`;
                    img.parentNode.replaceChild(placeholder, img);
                }
            });
            
            // Use Readability to extract clean content
            const documentClone = document.cloneNode(true);
            const reader = new Readability(documentClone);
            const article = reader.parse();
            
            if (!article) {
                // Fallback extraction
                const title = document.querySelector('h1, h2, [class*="title"]')?.textContent || '';
                const content = document.querySelector('[class*="content"], article, main, body')?.innerHTML || '';
                
                return {
                    title: title,
                    content: content,
                    textContent: document.body.textContent,
                    images: contentImages,
                    byline: '',
                    excerpt: ''
                };
            }
            
            return {
                title: article.title,
                content: article.content,
                textContent: article.textContent,
                byline: article.byline,
                excerpt: article.excerpt,
                siteName: article.siteName,
                images: contentImages
            };
        }
        """
    
    def _convert_to_markdown(self, article_data: Dict) -> str:
        """Convert extracted article to clean markdown with images"""
        import html2text
        
        # Configure html2text
        h = html2text.HTML2Text()
        h.body_width = 0  # Don't wrap
        h.ignore_links = False
        h.ignore_images = False
        h.unicode_snob = True
        
        # Convert HTML to markdown
        content_html = article_data.get('content', '')
        if not content_html:
            return article_data.get('textContent', '')
        
        # Convert to markdown
        markdown = h.handle(content_html)
        
        # Replace image placeholders with actual markdown images
        images = article_data.get('images', [])
        for img in images:
            placeholder = f"{{{{{img['parentId']}}}}}"
            img_markdown = f"![{img['alt']}]({img['src']})"
            markdown = markdown.replace(placeholder, img_markdown)
        
        # Clean up the markdown
        markdown = self._clean_markdown(markdown)
        
        # Add title if not already present
        title = article_data.get('title', '')
        if title and not markdown.startswith(f"# {title}"):
            markdown = f"# {title}\n\n{markdown}"
        
        # Add byline if present
        byline = article_data.get('byline', '')
        if byline:
            markdown = markdown.replace(f"# {title}", f"# {title}\n\n*{byline}*")
        
        return markdown
    
    def _clean_markdown(self, markdown: str) -> str:
        """Clean up markdown artifacts"""
        # Remove excessive newlines
        markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)
        
        # Remove empty table cells and artifacts
        markdown = re.sub(r'\|\s*\|\s*\|', '', markdown)
        markdown = re.sub(r'\|\s*---\s*\|\s*---\s*\|', '', markdown)
        
        # Remove invisible characters
        markdown = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF]', '', markdown)
        
        # Fix broken links
        markdown = re.sub(r'\[([^\]]+)\]\s+\(([^\)]+)\)', r'[\1](\2)', markdown)
        
        return markdown.strip()
    
    def _fallback_extraction(self, html_content: str) -> Dict:
        """Simple fallback if browser extraction fails"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove scripts and styles
        for element in soup(['script', 'style']):
            element.decompose()
        
        # Get text
        text = soup.get_text(separator='\n\n')
        
        # Find images
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and not any(x in src.lower() for x in ['track', 'pixel', '1x1']):
                images.append({
                    'src': src,
                    'alt': img.get('alt', 'Image')
                })
        
        return {
            'markdown': text,
            'images': images,
            'title': soup.find('h1').text if soup.find('h1') else '',
            'author': '',
            'excerpt': text[:200] if text else '',
            'word_count': len(text.split()) if text else 0
        }


# Convenience function for sync usage
def convert_html_to_markdown_sync(html_content: str, url: Optional[str] = None) -> str:
    """Synchronous wrapper for the async converter"""
    async def _convert():
        converter = PlaywrightConverter()
        try:
            result = await converter.convert_html_to_markdown(html_content, url)
            return result['markdown']
        finally:
            await converter.close()
    
    return asyncio.run(_convert())