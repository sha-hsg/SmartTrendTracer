"""
IMAP-based Substack Newsletter Collector
Alternative to Gmail API - uses IMAP with app password
"""
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import re
import os
from typing import List, Dict, Optional
from pathlib import Path

from bs4 import BeautifulSoup
import html2text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle, SubstackCollection

load_dotenv()

class IMAPSubstackCollector:
    """Collect Substack newsletters via IMAP"""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session or next(get_db())
        self.imap = None
        
        # HTML to Markdown converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0
        self.html_converter.protect_links = True
        
        # IMAP settings (can be configured via env vars)
        self.imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = int(os.getenv('IMAP_PORT', '993'))
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')  # App-specific password for Gmail
        
    def connect(self):
        """Connect to IMAP server"""
        if not self.email_address or not self.email_password:
            raise ValueError(
                "Email credentials not found!\n"
                "Please set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables.\n"
                "For Gmail:\n"
                "1. Enable 2-factor authentication\n"
                "2. Generate app-specific password at https://myaccount.google.com/apppasswords\n"
                "3. Add to .env file:\n"
                "   EMAIL_ADDRESS=your-email@gmail.com\n"
                "   EMAIL_PASSWORD=your-app-password"
            )
        
        try:
            # Connect to IMAP server
            self.imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.imap.login(self.email_address, self.email_password)
            print(f"✅ Connected to {self.email_address}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            raise
    
    def search_substack_emails(self, folder: str = 'INBOX', max_results: int = 50) -> List[int]:
        """Search for Substack emails"""
        try:
            # Select mailbox
            self.imap.select(folder)
            
            # Search for Substack emails
            # You can customize the search criteria:
            # - FROM "substack.com"
            # - UNSEEN (unread only)
            # - SINCE "01-Jan-2024"
            search_criteria = '(FROM "substack.com")'
            
            _, message_ids = self.imap.search(None, search_criteria)
            
            if message_ids[0]:
                # Get message IDs (newest first)
                ids = message_ids[0].split()
                ids.reverse()  # Newest first
                return ids[:max_results]
            
            return []
            
        except Exception as e:
            print(f"Error searching emails: {e}")
            return []
    
    def fetch_email(self, msg_id: int) -> Optional[Dict]:
        """Fetch and parse a single email"""
        try:
            # Fetch email data
            _, msg_data = self.imap.fetch(str(msg_id), '(RFC822)')
            
            # Parse email
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Extract headers
            subject = self._decode_header(email_message['Subject'])
            sender = self._decode_header(email_message['From'])
            date_str = email_message['Date']
            
            # Parse date
            try:
                from email.utils import parsedate_to_datetime
                date = parsedate_to_datetime(date_str)
            except:
                date = datetime.utcnow()
            
            # Extract body
            html_body = self._extract_html_body(email_message)
            
            # Parse content
            author_info = self._parse_author_from_sender(sender)
            article_info = self._parse_substack_html(html_body)
            
            return {
                'id': str(msg_id),
                'subject': subject,
                'sender': sender,
                'date': date,
                'html_body': html_body,
                'author': author_info,
                'article': article_info
            }
            
        except Exception as e:
            print(f"Error fetching email {msg_id}: {e}")
            return None
    
    def _decode_header(self, header_value: str) -> str:
        """Decode email header"""
        if not header_value:
            return ""
        
        decoded_parts = decode_header(header_value)
        result = []
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    result.append(part.decode(encoding, errors='ignore'))
                else:
                    result.append(part.decode('utf-8', errors='ignore'))
            else:
                result.append(part)
        
        return ' '.join(result)
    
    def _extract_html_body(self, email_message) -> str:
        """Extract HTML body from email"""
        html_body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                
                if content_type == "text/html":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        break
                    except:
                        html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            # Single part email
            if email_message.get_content_type() == "text/html":
                charset = email_message.get_content_charset() or 'utf-8'
                html_body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
        
        return html_body
    
    def _parse_author_from_sender(self, sender: str) -> Dict:
        """Parse author information from sender"""
        match = re.match(r'([^<]+)\s*<([^@]+)@([^>]+)>', sender)
        if match:
            name = match.group(1).strip()
            username = match.group(2).strip()
            domain = match.group(3).strip()
            
            if 'substack.com' in domain:
                subdomain = domain.replace('.substack.com', '')
            else:
                subdomain = username
            
            return {
                'name': name,
                'subdomain': subdomain,
                'email': f"{username}@{domain}"
            }
        
        return {'name': sender, 'subdomain': 'unknown', 'email': sender}
    
    def _parse_substack_html(self, html_body: str) -> Dict:
        """Parse Substack content from HTML"""
        if not html_body:
            return {}
        
        soup = BeautifulSoup(html_body, 'html.parser')
        
        # Extract title
        title = None
        for tag in ['h1', 'h2']:
            title_tag = soup.find(tag)
            if title_tag:
                title = title_tag.get_text(strip=True)
                break
        
        # Extract subtitle
        subtitle = None
        if title:
            subtitle_tag = soup.find('p', class_='subtitle') or soup.find('h3')
            if subtitle_tag:
                subtitle = subtitle_tag.get_text(strip=True)
        
        # Extract content
        content_div = soup.find('div', class_='body-text') or \
                     soup.find('div', class_='content') or \
                     soup.find('article') or \
                     soup.body
        
        if content_div:
            # Clean HTML
            for tag in content_div(['script', 'style']):
                tag.decompose()
            
            clean_html = str(content_div)
            markdown = self.html_converter.handle(clean_html)
            markdown = self._clean_markdown(markdown)
            
            preview = markdown[:500].strip() + '...' if len(markdown) > 500 else markdown
            word_count = len(markdown.split())
            reading_time = max(1, word_count // 200)
        else:
            markdown = ""
            preview = ""
            word_count = 0
            reading_time = 0
        
        # Extract URL
        url = None
        view_online_link = soup.find('a', string=re.compile('View online', re.I))
        if view_online_link:
            url = view_online_link.get('href')
        else:
            for link in soup.find_all('a', href=True):
                if 'substack.com/p/' in link['href']:
                    url = link['href']
                    break
        
        return {
            'title': title or 'Untitled',
            'subtitle': subtitle,
            'url': url,
            'content_html': html_body,
            'content_markdown': markdown,
            'preview': preview,
            'word_count': word_count,
            'reading_time_minutes': reading_time
        }
    
    def _clean_markdown(self, markdown: str) -> str:
        """Clean up markdown"""
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        patterns_to_remove = [
            r'Unsubscribe.*?$',
            r'View this email in your browser.*?$',
            r'You received this email because.*?$',
        ]
        
        for pattern in patterns_to_remove:
            markdown = re.sub(pattern, '', markdown, flags=re.MULTILINE | re.IGNORECASE)
        
        return markdown.strip()
    
    def save_article(self, email_data: Dict) -> Optional[SubstackArticle]:
        """Save article to database"""
        if not email_data or not email_data.get('article'):
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
        
        # Check if exists
        article_data = email_data['article']
        substack_id = f"imap_{email_data['id']}"
        
        existing = self.db.query(SubstackArticle).filter_by(
            substack_id=substack_id
        ).first()
        
        if existing:
            print(f"  Article already exists: {article_data.get('title', 'Untitled')[:50]}")
            return existing
        
        # Create article
        article = SubstackArticle(
            substack_id=substack_id,
            title=article_data.get('title', email_data['subject']),
            subtitle=article_data.get('subtitle'),
            url=article_data.get('url'),
            content_html=article_data.get('content_html'),
            content_markdown=article_data.get('content_markdown'),
            preview=article_data.get('preview'),
            word_count=article_data.get('word_count', 0),
            reading_time_minutes=article_data.get('reading_time_minutes', 1),
            author_id=author.id,
            published_at=email_data['date'],
            collected_at=datetime.utcnow()
        )
        
        self.db.add(article)
        return article
    
    def collect_newsletters(self, max_results: int = 50) -> int:
        """Main collection method"""
        print("📧 Connecting to email server...")
        
        # Create collection record
        collection = SubstackCollection(
            source='imap',
            status='running'
        )
        self.db.add(collection)
        self.db.flush()
        
        try:
            # Connect to IMAP
            self.connect()
            
            # Search for emails
            print("🔍 Searching for Substack newsletters...")
            message_ids = self.search_substack_emails(max_results=max_results)
            print(f"📬 Found {len(message_ids)} Substack emails")
            
            # Process emails
            articles_saved = 0
            for i, msg_id in enumerate(message_ids, 1):
                print(f"\n📖 Processing email {i}/{len(message_ids)}...")
                
                # Fetch email
                email_data = self.fetch_email(msg_id)
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
            
            # Update collection
            collection.completed_at = datetime.utcnow()
            collection.articles_collected = articles_saved
            collection.status = 'completed'
            self.db.commit()
            
            # Disconnect
            if self.imap:
                self.imap.logout()
            
            print(f"\n✅ Collection complete! Saved {articles_saved} new articles")
            return articles_saved
            
        except Exception as e:
            print(f"❌ Error: {e}")
            collection.status = 'failed'
            collection.error_message = str(e)
            self.db.commit()
            raise

def main():
    """Run collector from command line"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect Substack via IMAP')
    parser.add_argument('--max', type=int, default=50, help='Max emails to process')
    parser.add_argument('--test', action='store_true', help='Test connection only')
    
    args = parser.parse_args()
    
    collector = IMAPSubstackCollector()
    
    if args.test:
        print("Testing IMAP connection...")
        if collector.connect():
            emails = collector.search_substack_emails(max_results=5)
            print(f"✅ Connection successful! Found {len(emails)} Substack emails")
            collector.imap.logout()
    else:
        articles = collector.collect_newsletters(args.max)
        
        # Show summary
        db = next(get_db())
        total = db.query(SubstackArticle).count()
        authors = db.query(SubstackAuthor).count()
        
        print(f"\n📊 Database Summary:")
        print(f"  Total articles: {total}")
        print(f"  Total authors: {authors}")

if __name__ == "__main__":
    main()