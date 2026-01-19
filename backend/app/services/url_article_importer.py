"""
Service for importing articles from URLs with cleaning and processing
"""

import re
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple
from bs4 import BeautifulSoup
from markdownify import markdownify
from urllib.parse import urlparse

class URLArticleImporter:
    """Import and process articles from web URLs"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def import_from_url(self, url: str) -> Dict:
        """
        Import an article from a URL
        
        Args:
            url: The URL to import from
            
        Returns:
            Dict with article data and import status
        """
        try:
            # Check if article already exists
            existing = self.db.query(SubstackArticle).filter_by(url=url).first()
            if existing:
                return {
                    'success': False,
                    'error': 'Article already exists in database',
                    'article_id': existing.id
                }
            
            # Fetch the webpage
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, timeout=30)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract metadata based on platform
            if 'substack.com' in url or self._is_substack_site(soup):
                article_data = self._extract_substack_article(soup, url)
            else:
                # Generic article extraction
                article_data = self._extract_generic_article(soup, url)
            
            # Clean and process the content
            cleaned_content = self._clean_article_content(article_data['content_html'])
            
            # Convert to markdown
            markdown_content = self._html_to_markdown(cleaned_content)
            
            # Clean markdown footers
            markdown_content = self._clean_markdown_footers(markdown_content)
            
            # Get or create author
            author = self._get_or_create_author(article_data['author_info'])
            
            # Create the article
            article = SubstackArticle(
                author_id=author.id,
                title=article_data['title'],
                subtitle=article_data.get('subtitle'),
                substack_id=f"url_import_{datetime.now().isoformat()}",
                slug=self._generate_slug(article_data['title']),
                url=url,
                content_html=cleaned_content,
                content_markdown=markdown_content,
                preview=self._generate_preview(markdown_content),
                published_at=article_data.get('published_at', datetime.now()),
                word_count=len(markdown_content.split()),
                reading_time_minutes=max(1, len(markdown_content.split()) // 200),
                processed=True,
                deleted=False
            )
            
            self.db.add(article)
            self.db.commit()
            
            return {
                'success': True,
                'article_id': article.id,
                'title': article.title,
                'author': author.name,
                'word_count': article.word_count
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Failed to fetch URL: {str(e)}'
            }
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': f'Failed to import article: {str(e)}'
            }
    
    def _is_substack_site(self, soup: BeautifulSoup) -> bool:
        """Check if the site is a Substack publication"""
        # Check for Substack-specific meta tags or elements
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            content = tag.get('content', '')
            if 'substack' in content.lower():
                return True
        
        # Check for Substack-specific classes
        substack_indicators = [
            'portable-text-block',
            'post-content',
            'available-content',
            'body markup'
        ]
        
        for indicator in substack_indicators:
            if soup.find(class_=indicator):
                return True
                
        return False
    
    def _extract_substack_article(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract article data from a Substack page"""
        data = {}
        
        # Title - try multiple selectors
        title = None
        title_selectors = [
            'h1.post-title',
            'h1[class*="title"]',
            'meta[property="og:title"]',
            'title'
        ]
        
        for selector in title_selectors:
            if selector.startswith('meta'):
                elem = soup.find(selector.split('[')[0], {selector.split('=')[0].split('[')[1]: selector.split('=')[1].strip('"]')})
                if elem:
                    title = elem.get('content')
            else:
                elem = soup.select_one(selector)
                if elem:
                    title = elem.get_text(strip=True)
            if title:
                break
        
        data['title'] = title or 'Untitled Article'
        
        # Subtitle
        subtitle_elem = soup.select_one('h3.subtitle, p.subtitle, h2.post-subtitle')
        data['subtitle'] = subtitle_elem.get_text(strip=True) if subtitle_elem else None
        
        # Author
        author_info = self._extract_author_info(soup, url)
        data['author_info'] = author_info
        
        # Published date
        date_elem = soup.select_one('time, .post-date, meta[property="article:published_time"]')
        if date_elem:
            if date_elem.name == 'meta':
                date_str = date_elem.get('content')
            else:
                date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            data['published_at'] = self._parse_date(date_str)
        else:
            data['published_at'] = datetime.now()
        
        # Content - try multiple content selectors
        content_selectors = [
            'div.available-content',
            'div.post-content',
            'div.body.markup',
            'div.portable-text-block',
            'article',
            'main'
        ]
        
        content_html = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content_html = str(content_elem)
                break
        
        if not content_html:
            # Fallback: get the body content
            body = soup.find('body')
            if body:
                content_html = str(body)
        
        data['content_html'] = content_html or '<p>Content could not be extracted</p>'
        
        return data
    
    def _extract_generic_article(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract article data from a generic webpage"""
        data = {}
        
        # Title - use Open Graph or standard title
        og_title = soup.find('meta', property='og:title')
        if og_title:
            data['title'] = og_title.get('content')
        else:
            title_elem = soup.find('title')
            data['title'] = title_elem.get_text(strip=True) if title_elem else urlparse(url).netloc
        
        # Subtitle/Description
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            data['subtitle'] = og_desc.get('content')
        else:
            meta_desc = soup.find('meta', {'name': 'description'})
            data['subtitle'] = meta_desc.get('content') if meta_desc else None
        
        # Author
        author_info = self._extract_author_info(soup, url)
        data['author_info'] = author_info
        
        # Published date
        date_meta = soup.find('meta', property='article:published_time')
        if date_meta:
            data['published_at'] = self._parse_date(date_meta.get('content'))
        else:
            data['published_at'] = datetime.now()
        
        # Content - try to find main content area
        # Remove navigation, headers, footers, sidebars
        for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style']):
            tag.decompose()
        
        # Try to find main content
        content_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.content',
            '#content',
            '.post-content',
            '.entry-content'
        ]
        
        content_html = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content_html = str(content_elem)
                break
        
        if not content_html:
            # Fallback: use body
            body = soup.find('body')
            content_html = str(body) if body else '<p>Content could not be extracted</p>'
        
        data['content_html'] = content_html
        
        return data
    
    def _extract_author_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract author information from the page"""
        author_name = None
        
        # Try meta tags first
        author_meta = soup.find('meta', {'name': 'author'}) or \
                     soup.find('meta', property='article:author')
        if author_meta:
            author_name = author_meta.get('content')
        
        # Try common author selectors
        if not author_name:
            author_selectors = [
                '.author-name',
                '.by-author',
                '.post-author',
                'span[itemprop="author"]',
                'a[rel="author"]'
            ]
            
            for selector in author_selectors:
                elem = soup.select_one(selector)
                if elem:
                    author_name = elem.get_text(strip=True)
                    break
        
        # Extract domain as fallback
        domain = urlparse(url).netloc.replace('www.', '').split('.')[0]
        
        return {
            'name': author_name or domain.title(),
            'subdomain': domain,
            'url': f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        }
    
    def _clean_article_content(self, html: str) -> str:
        """Clean the article HTML content while preserving structure for markdown conversion"""
        if not html:
            return html
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements but keep structure
        unwanted_selectors = [
            '.share-buttons', '.social-share', '.sharing',  # Social buttons
            '.subscribe-widget', '.subscription-form', '.subscribe-cta',  # Subscription CTAs
            '.comments', '#comments', '.comment-section',  # Comments
            '.related-posts', '.recommended',  # Related content
            'script', 'style', 'iframe',  # Scripts and styles
            '.advertisement', '.ads', '.ad-container',  # Ads
            'footer', 'nav', '.navigation',  # Navigation elements
            '.cookie-banner', '.popup',  # Popups
        ]
        
        for selector in unwanted_selectors:
            for elem in soup.select(selector):
                elem.decompose()
        
        # Remove tracking pixels
        for img in soup.find_all('img'):
            src = img.get('src', '')
            width = img.get('width')
            height = img.get('height')
            
            if (width == '1' and height == '1') or \
               'tracking' in src or \
               '/track' in src or \
               'pixel' in src:
                img.decompose()
        
        # Clean attributes but preserve structure
        for tag in soup.find_all():
            # Keep only essential attributes
            if tag.name == 'a':
                href = tag.get('href', '')
                tag.attrs = {'href': href} if href else {}
            elif tag.name == 'img':
                src = tag.get('src', '')
                alt = tag.get('alt', '')
                tag.attrs = {'src': src, 'alt': alt}
            else:
                # Remove all attributes for other tags (keeps structure)
                tag.attrs = {}
        
        # Return the cleaned HTML (NOT plain text) for markdown conversion
        return str(soup)
    
    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown"""
        if not html:
            return ""
        
        # Configure markdownify
        markdown = markdownify(
            html,
            heading_style="ATX",
            bullets="-",
            strong_em_symbol="**",
            wrap=True,
            wrap_width=80
        )
        
        # Clean up excessive newlines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        return markdown.strip()
    
    def _clean_markdown_footers(self, markdown: str) -> str:
        """Remove common footer patterns from markdown"""
        if not markdown:
            return markdown
        
        # Patterns to remove
        footer_patterns = [
            # Substack footers
            r'Thanks for reading.*?$',
            r'Subscribe to.*?$',
            r'Share this post.*?$',
            r'Leave a comment.*?$',
            r'Start writing on Substack.*?$',
            r'Get the app.*?$',
            
            # Copyright and author attribution
            r'©\s*\d{4}.*?$',
            r'Copyright.*?$',
            r'All rights reserved.*?$',
            
            # Social media CTAs
            r'Follow me on.*?$',
            r'Connect with me.*?$',
            r'Find me on.*?$',
            
            # Newsletter CTAs
            r'Sign up for.*?$',
            r'Get my newsletter.*?$',
            r'Subscribe for free.*?$'
        ]
        
        # Apply each pattern
        for pattern in footer_patterns:
            markdown = re.sub(pattern, '', markdown, flags=re.MULTILINE | re.IGNORECASE)
        
        # Remove trailing whitespace and excessive newlines
        markdown = markdown.strip()
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        return markdown
    
    def _get_or_create_author(self, author_info: Dict) -> SubstackAuthor:
        """Get existing author or create new one"""
        # Check if author exists by subdomain
        author = self.db.query(SubstackAuthor).filter_by(
            subdomain=author_info['subdomain']
        ).first()
        
        if not author:
            # Create new author
            author = SubstackAuthor(
                name=author_info['name'],
                subdomain=author_info['subdomain'],
                url=author_info['url'],
                email=f"{author_info['subdomain']}@imported.com"  # Placeholder email
            )
            self.db.add(author)
            self.db.commit()
        
        return author
    
    def _generate_slug(self, title: str) -> str:
        """Generate a URL-friendly slug from title"""
        # Convert to lowercase and replace spaces with hyphens
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:200]  # Limit length
    
    def _generate_preview(self, markdown: str, length: int = 300) -> str:
        """Generate a preview from markdown content"""
        # Remove markdown formatting for preview
        preview = re.sub(r'#+ ', '', markdown)  # Headers
        preview = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', preview)  # Bold/italic
        preview = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', preview)  # Links
        preview = re.sub(r'`([^`]+)`', r'\1', preview)  # Code
        preview = re.sub(r'\n+', ' ', preview)  # Newlines to spaces
        
        # Truncate to length
        if len(preview) > length:
            preview = preview[:length].rsplit(' ', 1)[0] + '...'
        
        return preview.strip()
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        
        # Try dateutil parser as fallback
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except:
            return None