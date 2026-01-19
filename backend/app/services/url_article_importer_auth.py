"""
Enhanced URL Article Importer with authentication support
"""

import re
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple
from bs4 import BeautifulSoup
from markdownify import markdownify
from urllib.parse import urlparse

class AuthenticatedURLImporter:
    """Import articles from URLs with authentication support"""
    
    def __init__(self, db: Session):
        self.db = db
        self.session = requests.Session()
        
    def login_substack(self, email: str, password: str) -> bool:
        """
        Login to Substack to access subscriber content
        
        Args:
            email: Substack account email
            password: Substack account password
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # First, get the login page to extract CSRF token
            login_url = "https://substack.com/sign-in"
            response = self.session.get(login_url)
            
            # Login via API endpoint
            api_login_url = "https://substack.com/api/v1/login"
            login_data = {
                "email": email,
                "password": password,
                "captcha_response": None
            }
            
            response = self.session.post(
                api_login_url,
                json=login_data,
                headers={
                    "Content-Type": "application/json",
                    "Origin": "https://substack.com",
                    "Referer": "https://substack.com/sign-in"
                }
            )
            
            if response.status_code == 200:
                print("✅ Successfully logged in to Substack")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def import_from_url(self, url: str, use_auth: bool = False) -> Dict:
        """
        Import an article from a URL with optional authentication
        
        Args:
            url: The URL to import from
            use_auth: Whether to use authenticated session
            
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
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            if use_auth:
                # Use authenticated session
                response = self.session.get(url, headers=headers, timeout=30)
            else:
                # Regular request
                response = requests.get(url, headers=headers, timeout=30)
                
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if we got the full article or just preview
            paywall_elements = soup.select('.paywall, .subscription-widget, .subscribe-prompt')
            if paywall_elements and not use_auth:
                print("⚠️ Paywall detected - article may be truncated. Consider using authentication.")
            
            # Extract metadata based on platform
            if 'substack.com' in url or self._is_substack_site(soup):
                article_data = self._extract_substack_article(soup, url)
            else:
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
                'word_count': article.word_count,
                'full_content': not bool(paywall_elements) or use_auth
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
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            content = tag.get('content', '')
            if 'substack' in content.lower():
                return True
        
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
        
        # Title
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
        
        # Content - look for full content first, then available content
        content_selectors = [
            'div.body.markup',  # Full article content
            'div.post-content',  # Alternative full content
            'div[class*="post-content"]',  # Any post-content class
            'div.available-content',  # Preview/available content
            'div.portable-text-block',
            'article',
            'main'
        ]
        
        content_html = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Check if this looks like substantial content
                text_length = len(content_elem.get_text(strip=True))
                if text_length > 500:  # Minimum reasonable article length
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
        
        # Title
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
        
        # Content
        for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style']):
            tag.decompose()
        
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
        """Clean the article HTML content while preserving structure"""
        if not html:
            return html
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements but keep structure
        unwanted_selectors = [
            '.share-buttons', '.social-share', '.sharing',
            '.subscribe-widget', '.subscription-form', '.subscribe-cta',
            '.comments', '#comments', '.comment-section',
            '.related-posts', '.recommended',
            'script', 'style', 'iframe',
            '.advertisement', '.ads', '.ad-container',
            'footer', 'nav', '.navigation',
            '.cookie-banner', '.popup',
            '.paywall-cta', '.upgrade-prompt'  # Paywall CTAs
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
            if tag.name == 'a':
                href = tag.get('href', '')
                tag.attrs = {'href': href} if href else {}
            elif tag.name == 'img':
                src = tag.get('src', '')
                alt = tag.get('alt', '')
                tag.attrs = {'src': src, 'alt': alt}
            else:
                tag.attrs = {}
        
        return str(soup)
    
    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown"""
        if not html:
            return ""
        
        markdown = markdownify(
            html,
            heading_style="ATX",
            bullets="-",
            strong_em_symbol="**",
            wrap=True,
            wrap_width=80
        )
        
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        return markdown.strip()
    
    def _clean_markdown_footers(self, markdown: str) -> str:
        """Remove common footer patterns from markdown"""
        if not markdown:
            return markdown
        
        footer_patterns = [
            r'Thanks for reading.*?$',
            r'Subscribe to.*?$',
            r'Share this post.*?$',
            r'Leave a comment.*?$',
            r'Start writing on Substack.*?$',
            r'Get the app.*?$',
            r'©\s*\d{4}.*?$',
            r'Copyright.*?$',
            r'All rights reserved.*?$',
            r'Follow me on.*?$',
            r'Connect with me.*?$',
            r'Find me on.*?$',
            r'Sign up for.*?$',
            r'Get my newsletter.*?$',
            r'Subscribe for free.*?$'
        ]
        
        for pattern in footer_patterns:
            markdown = re.sub(pattern, '', markdown, flags=re.MULTILINE | re.IGNORECASE)
        
        markdown = markdown.strip()
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        return markdown
    
    def _get_or_create_author(self, author_info: Dict) -> SubstackAuthor:
        """Get existing author or create new one"""
        author = self.db.query(SubstackAuthor).filter_by(
            subdomain=author_info['subdomain']
        ).first()
        
        if not author:
            author = SubstackAuthor(
                name=author_info['name'],
                subdomain=author_info['subdomain'],
                url=author_info['url'],
                email=f"{author_info['subdomain']}@imported.com"
            )
            self.db.add(author)
            self.db.commit()
        
        return author
    
    def _generate_slug(self, title: str) -> str:
        """Generate a URL-friendly slug from title"""
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:200]
    
    def _generate_preview(self, markdown: str, length: int = 300) -> str:
        """Generate a preview from markdown content"""
        preview = re.sub(r'#+ ', '', markdown)
        preview = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', preview)
        preview = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', preview)
        preview = re.sub(r'`([^`]+)`', r'\1', preview)
        preview = re.sub(r'\n+', ' ', preview)
        
        if len(preview) > length:
            preview = preview[:length].rsplit(' ', 1)[0] + '...'
        
        return preview.strip()
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_str:
            return None
        
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
        
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except:
            return None