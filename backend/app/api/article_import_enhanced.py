"""
Enhanced article import API with cookie authentication support
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser

from app.services.url_article_importer import URLArticleImporter
from app.services.curl_parser import parse_curl_command, extract_cookies_from_curl

router = APIRouter()

def extract_publication_date(soup: BeautifulSoup) -> datetime:
    """
    Extract publication date from Substack article HTML
    """
    import json
    import re
    
    # First, try to get date from JSON-LD structured data
    json_ld = soup.find('script', type='application/ld+json')
    if json_ld:
        try:
            data = json.loads(json_ld.string)
            if 'datePublished' in data:
                return date_parser.parse(data['datePublished'])
        except:
            pass
    
    # Try multiple selectors for date
    date_selectors = [
        'time[datetime]',  # Standard time element with datetime attribute
        'div.post-header time',  # In post header
        'div.pencraft time',  # Pencraft theme
        'span.post-meta-item time',  # Post meta
        'div.post-date',  # Simple date div
        'div.meta-EgzBVA',  # Substack meta class
    ]
    
    for selector in date_selectors:
        date_elem = soup.select_one(selector)
        if date_elem:
            # Try to get datetime attribute first
            if date_elem.has_attr('datetime'):
                try:
                    return date_parser.parse(date_elem['datetime'])
                except:
                    pass
            
            # Try to parse the text content
            date_text = date_elem.get_text(strip=True)
            if date_text:
                # Look for date pattern in the text
                date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}'
                date_match = re.search(date_pattern, date_text)
                if date_match:
                    try:
                        return date_parser.parse(date_match.group(0))
                    except:
                        pass
    
    # Fallback: look for date patterns in meta tags
    meta_date = soup.find('meta', {'property': 'article:published_time'})
    if meta_date and meta_date.get('content'):
        try:
            return date_parser.parse(meta_date['content'])
        except:
            pass
    
    # Last resort: look for date in text like "Jan 14, 2024" in first 10000 chars
    date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}'
    date_match = re.search(date_pattern, str(soup)[:10000])
    if date_match:
        try:
            return date_parser.parse(date_match.group(0))
        except:
            pass
    
    # If all else fails, use current date
    print("Warning: Could not extract publication date, using current date")
    return datetime.now()

class URLImportRequest(BaseModel):
    url: HttpUrl
    cookies: Optional[str] = None  # Cookie string from browser
    
class CookieImportRequest(BaseModel):
    url: HttpUrl
    curl_command: Optional[str] = None  # cURL command from browser
    cookie_json: Optional[str] = None  # JSON cookie array from extension
    
class ImportResponse(BaseModel):
    success: bool
    article_id: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    word_count: Optional[int] = None
    content_increase: Optional[str] = None
    error: Optional[str] = None
    requires_auth: Optional[bool] = None

@router.post("/import-with-cookies", response_model=ImportResponse)
def import_article_with_cookies(
    request: CookieImportRequest,
):
    """
    Import an article using browser cookies for authentication
    
    This endpoint accepts a cURL command copied from browser DevTools
    and extracts the cookies to fetch subscriber-only content.
    """
    
    try:
        cookies = {}
        
        # Check if JSON cookies were provided (from Copy Cookie extension)
        if request.cookie_json:
            import json
            print(f"Received JSON cookies")
            try:
                cookie_list = json.loads(request.cookie_json)
                for cookie in cookie_list:
                    # Extract name and value from each cookie object
                    if 'name' in cookie and 'value' in cookie:
                        # URL decode the value if needed
                        from urllib.parse import unquote
                        cookies[cookie['name']] = unquote(cookie['value'])
                print(f"Parsed {len(cookies)} cookies from JSON")
                print(f"Cookie keys: {list(cookies.keys())[:5]}")
            except json.JSONDecodeError as e:
                return ImportResponse(
                    success=False,
                    error=f"Invalid JSON format for cookies: {str(e)}",
                    requires_auth=True
                )
        # Otherwise parse from cURL command
        elif request.curl_command:
            # Parse cookies from cURL command using the robust parser
            print(f"Received cURL command length: {len(request.curl_command)}")
            
            # Use the new parser
            parsed_url, cookies, headers = parse_curl_command(request.curl_command)
            
            # Use the URL from the cURL if not provided separately
            if not request.url and parsed_url:
                request.url = parsed_url
            
            if not cookies:
                # Try the simple extraction as fallback
                cookies = extract_cookies_from_curl(request.curl_command)
            
            if not cookies:
                # Provide helpful error message
                available_headers = list(headers.keys()) if headers else []
                return ImportResponse(
                    success=False,
                    error=f"No cookies found in cURL command. Headers found: {available_headers[:5]}. Make sure you're logged in and copy the full cURL command from Network tab.",
                    requires_auth=True
                )
            
            print(f"Found {len(cookies)} cookies")
            print(f"Cookie keys: {list(cookies.keys())[:5]}")
        else:
            return ImportResponse(
                success=False,
                error="No cookies provided. Please provide either cURL command or JSON cookies.",
                requires_auth=True
            )
        
        # Create session with cookies
        session = requests.Session()
        session.cookies.update(cookies)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Fetch the article with timeout
        print(f"Fetching article from: {request.url}")
        response = session.get(str(request.url), timeout=30)
        print(f"Response status: {response.status_code}")
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if we got full content
        paywall = soup.select_one('.paywall')
        is_full_content = not bool(paywall)
        
        # Find content
        content_elem = (
            soup.select_one('div.body.markup') or 
            soup.select_one('div.available-content') or
            soup.select_one('article.post div.body')
        )
        
        if not content_elem:
            return ImportResponse(
                success=False,
                error="Could not find article content on the page",
                requires_auth=True
            )
        
        # Check for existing article
        existing = db.query(SubstackArticle).filter_by(url=str(request.url)).first()
        old_word_count = existing.word_count if existing else 0
        
        if existing:
            db.delete(existing)
            db.commit()
        
        # Process content
        importer = URLArticleImporter(db)
        
        # Clean and convert
        cleaned_html = importer._clean_article_content(str(content_elem))
        markdown_content = importer._html_to_markdown(cleaned_html)
        markdown_content = importer._clean_markdown_footers(markdown_content)
        
        # Extract metadata
        title = soup.find('h1', class_='post-title')
        title_text = title.get_text(strip=True) if title else "Untitled"
        
        subtitle = soup.find('h3', class_='subtitle')
        subtitle_text = subtitle.get_text(strip=True) if subtitle else None
        
        # Extract author
        author_elem = soup.select_one('.profile-hover-card-target a, .author-name')
        author_name = author_elem.get_text(strip=True) if author_elem else "Unknown"
        
        # Extract publication date
        published_date = extract_publication_date(soup)
        print(f"Extracted publication date: {published_date}")
        
        # Get or create author
        from urllib.parse import urlparse
        domain = urlparse(str(request.url)).netloc.replace('www.', '').split('.')[0]
        
        author = db.query(SubstackAuthor).filter_by(subdomain=domain).first()
        if not author:
            author = SubstackAuthor(
                name=author_name,
                subdomain=domain,
                url=f"https://{urlparse(str(request.url)).netloc}",
                email=f"{domain}@imported.com"
            )
            db.add(author)
            db.commit()
        
        # Create article
        article = SubstackArticle(
            author_id=author.id,
            title=title_text,
            subtitle=subtitle_text,
            substack_id=f"cookie_import_{datetime.now().isoformat()}",
            slug=importer._generate_slug(title_text),
            url=str(request.url),
            content_html=cleaned_html,
            content_markdown=markdown_content,
            preview=importer._generate_preview(markdown_content),
            published_at=published_date,
            word_count=len(markdown_content.split()),
            reading_time_minutes=max(1, len(markdown_content.split()) // 200),
            processed=True,
            deleted=False
        )
        
        db.add(article)
        db.commit()
        
        # Calculate improvement
        content_increase = None
        if old_word_count > 0:
            increase_pct = ((article.word_count - old_word_count) / old_word_count) * 100
            if increase_pct > 0:
                content_increase = f"+{increase_pct:.0f}% more content"
        
        return ImportResponse(
            success=True,
            article_id=article.id,
            title=article.title,
            author=author.name,
            word_count=article.word_count,
            content_increase=content_increase,
            requires_auth=False
        )
        
    except requests.RequestException as e:
        return ImportResponse(
            success=False,
            error=f"Failed to fetch article: {str(e)}",
            requires_auth=True
        )
    except Exception as e:
        db.rollback()
        return ImportResponse(
            success=False,
            error=f"Import failed: {str(e)}",
            requires_auth=False
        )

@router.post("/check-paywall")
    """
    Check if an article is behind a paywall
    """
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for paywall indicators
        paywall_indicators = [
            '.paywall',
            '.subscription-widget',
            '.subscribe-prompt',
            'button[data-testid="paywall-subscribe-button"]',
            'div[class*="paywall"]'
        ]
        
        has_paywall = any(soup.select_one(indicator) for indicator in paywall_indicators)
        
        # Check content length
        content_elem = soup.select_one('div.body.markup, div.available-content')
        content_length = len(content_elem.get_text(strip=True)) if content_elem else 0
        
        # Check if "This post is for paid subscribers" text exists
        page_text = soup.get_text().lower()
        needs_subscription = "this post is for paid subscribers" in page_text
        
        return {
            "url": url,
            "has_paywall": has_paywall,
            "needs_subscription": needs_subscription,
            "content_preview_length": content_length,
            "is_truncated": content_length < 5000 and (has_paywall or needs_subscription)
        }
        
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "has_paywall": None
        }

@router.post("/import-basic", response_model=ImportResponse)
def import_article_basic(
    request: URLImportRequest,
):
    """
    Basic article import without authentication
    """
    try:
        importer = URLArticleImporter(db)
        result = importer.import_from_url(str(request.url))
        
        if result['success']:
            return ImportResponse(
                success=True,
                article_id=result.get('article_id'),
                title=result.get('title'),
                author=result.get('author'),
                word_count=result.get('word_count'),
                requires_auth=False
            )
        else:
            return ImportResponse(
                success=False,
                error=result.get('error', 'Import failed'),
                requires_auth=result.get('is_truncated', False)
            )
    except Exception as e:
        return ImportResponse(
            success=False,
            error=str(e),
            requires_auth=False
        )

@router.post("/import-with-cookie-string", response_model=ImportResponse)  
def import_article_with_cookie_string(
    request: URLImportRequest,
):
    """
    Import an article using a raw cookie string
    
    The cookie string should be in the format:
    "cookie_name1=value1; cookie_name2=value2; ..."
    """
    if not request.cookies:
        return ImportResponse(
            success=False,
            error="No cookies provided",
            requires_auth=True
        )
    
    try:
        # Parse cookies into dict
        cookies = {}
        for cookie in request.cookies.split('; '):
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key] = value
        
        # Create session with cookies
        session = requests.Session()
        session.cookies.update(cookies)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Fetch the article with timeout
        print(f"Fetching article from: {request.url}")
        response = session.get(str(request.url), timeout=30)
        print(f"Response status: {response.status_code}")
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find content
        content_elem = (
            soup.select_one('div.body.markup') or 
            soup.select_one('div.available-content') or
            soup.select_one('article.post div.body')
        )
        
        if not content_elem:
            return ImportResponse(
                success=False,
                error="Could not find article content on the page",
                requires_auth=True
            )
        
        # Check for existing article
        existing = db.query(SubstackArticle).filter_by(url=str(request.url)).first()
        old_word_count = existing.word_count if existing else 0
        
        if existing:
            db.delete(existing)
            db.commit()
        
        # Process content
        importer = URLArticleImporter(db)
        
        # Clean and convert
        cleaned_html = importer._clean_article_content(str(content_elem))
        markdown_content = importer._html_to_markdown(cleaned_html)
        markdown_content = importer._clean_markdown_footers(markdown_content)
        
        # Extract metadata
        title = soup.find('h1', class_='post-title')
        title_text = title.get_text(strip=True) if title else "Untitled"
        
        subtitle = soup.find('h3', class_='subtitle')
        subtitle_text = subtitle.get_text(strip=True) if subtitle else None
        
        # Extract author
        author_elem = soup.select_one('.profile-hover-card-target a, .author-name')
        author_name = author_elem.get_text(strip=True) if author_elem else "Unknown"
        
        # Extract publication date
        published_date = extract_publication_date(soup)
        print(f"Extracted publication date: {published_date}")
        
        # Get or create author
        from urllib.parse import urlparse
        domain = urlparse(str(request.url)).netloc.replace('www.', '').split('.')[0]
        
        author = db.query(SubstackAuthor).filter_by(subdomain=domain).first()
        if not author:
            author = SubstackAuthor(
                name=author_name,
                subdomain=domain,
                url=f"https://{urlparse(str(request.url)).netloc}",
                email=f"{domain}@imported.com"
            )
            db.add(author)
            db.commit()
        
        # Create article
        article = SubstackArticle(
            author_id=author.id,
            title=title_text,
            subtitle=subtitle_text,
            substack_id=f"cookie_import_{datetime.now().isoformat()}",
            slug=importer._generate_slug(title_text),
            url=str(request.url),
            content_html=cleaned_html,
            content_markdown=markdown_content,
            preview=importer._generate_preview(markdown_content),
            published_at=published_date,
            word_count=len(markdown_content.split()),
            reading_time_minutes=max(1, len(markdown_content.split()) // 200),
            processed=True,
            deleted=False
        )
        
        db.add(article)
        db.commit()
        
        # Calculate improvement
        content_increase = None
        if old_word_count > 0:
            increase_pct = ((article.word_count - old_word_count) / old_word_count) * 100
            if increase_pct > 0:
                content_increase = f"+{increase_pct:.0f}% more content"
        
        return ImportResponse(
            success=True,
            article_id=article.id,
            title=article.title,
            author=author.name,
            word_count=article.word_count,
            content_increase=content_increase,
            requires_auth=False
        )
        
    except requests.RequestException as e:
        return ImportResponse(
            success=False,
            error=f"Failed to fetch article: {str(e)}",
            requires_auth=True
        )
    except Exception as e:
        db.rollback()
        return ImportResponse(
            success=False,
            error=f"Import failed: {str(e)}",
            requires_auth=False
        )