"""
Gmail-based Substack Newsletter Collector
Fetches Substack newsletters from Gmail and converts them to Markdown
"""
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

from googleapiclient.errors import HttpError

from app.collectors.gmail_auth import authenticate_gmail
from app.collectors.substack_parser import SubstackParser, remove_substack_footer
from app.database.mongodb import get_database


class GmailSubstackCollector:
    """Collect Substack newsletters from Gmail"""

    def __init__(self):
        self.service = None
        self.parser = SubstackParser()
        self.db = get_database()

    def authenticate(self, credentials_file: str = 'credentials.json', token_file: str = 'token.pickle'):
        """Authenticate with Gmail API"""
        self.service = authenticate_gmail(credentials_file, token_file)
        return True

    def search_substack_emails(self, query: str = 'from:substack.com OR "from Marcus on AI" OR "from One Useful Thing"', max_results: int = 100) -> List[str]:
        """Search for Substack emails in Gmail"""
        try:
            # You can customize the query:
            # - 'from:substack.com' - all Substack emails
            # - 'from:substack.com is:unread' - only unread
            # - 'from:substack.com after:2024/1/1' - after specific date
            # - 'label:Substack' - if you've labeled them

            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            # Get additional pages if needed
            while 'nextPageToken' in results and len(messages) < max_results:
                page_token = results['nextPageToken']
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=min(100, max_results - len(messages)),
                    pageToken=page_token
                ).execute()
                messages.extend(results.get('messages', []))

            return [msg['id'] for msg in messages]

        except HttpError as error:
            logger.error(f"Gmail API error searching messages: {error}")
            return []

    def get_email_content(self, msg_id: str) -> Dict:
        """Get email content and metadata"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()

            # Extract metadata from headers
            headers = message['payload'].get('headers', [])
            header_dict = {h['name']: h['value'] for h in headers}

            # Get email metadata
            subject = header_dict.get('Subject', '')
            sender = header_dict.get('From', '')
            date_str = header_dict.get('Date', '')

            # Parse date
            try:
                # Gmail date format: "Thu, 7 Nov 2024 08:30:00 +0000"
                from email.utils import parsedate_to_datetime
                date = parsedate_to_datetime(date_str)
            except (ValueError, TypeError):
                date = datetime.now(timezone.utc)

            # Extract HTML body
            html_body = self.parser.extract_html_body(message['payload'])

            # Parse Substack-specific metadata
            author_info = self.parser.parse_author_from_sender(sender, html_body)

            # Check if article already exists first (to suppress warnings on re-collection)
            substack_id = f"gmail_{msg_id}"
            existing = self.db.articles.find_one({'substack_id': substack_id})

            # Clean forwarded email artifacts before parsing
            cleaned_html = self.parser.clean_forwarded_content(html_body)
            # Pass check_only=True if article already exists to suppress warnings
            article_info = self.parser.parse_substack_html(cleaned_html, check_only=(existing is not None))

            return {
                'id': msg_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'html_body': html_body,
                'author': author_info,
                'article': article_info
            }

        except HttpError as error:
            logger.error(f"Error fetching message {msg_id}: {error}")
            return None

    def save_article(self, email_data: Dict) -> Optional[Dict]:
        """Save article to database"""
        if not email_data or not email_data.get('article'):
            return None

        # Validate that this is from an expected author (configured authors + direct Substack subscriptions)
        author_info = email_data['author']
        expected_emails = ['robotic@substack.com', 'garymarcus@substack.com', 'sebastianraschka@substack.com']

        # Also allow direct Substack subscriptions (emails ending with @substack.com)
        is_direct_substack = author_info['email'].endswith('@substack.com')
        is_configured_forwarded = author_info['email'] in expected_emails

        if not (is_direct_substack or is_configured_forwarded):
            print(f"  ⚠️  Skipping article from unexpected author: {author_info['name']} ({author_info['email']})")
            return None

        # Get or create author
        author_info = email_data['author']
        author = self.db.substack_authors.find_one({'subdomain': author_info['subdomain']})

        if not author:
            author_doc = {
                'subdomain': author_info['subdomain'],
                'name': author_info['name'],
                'email': author_info.get('email'),
                'url': f"https://{author_info['subdomain']}.substack.com",
                'created_at': datetime.now(timezone.utc),
            }
            result = self.db.substack_authors.insert_one(author_doc)
            author_doc['_id'] = result.inserted_id
            author = author_doc

        # Check if article already exists
        article_data = email_data['article']

        # Create unique ID from email ID
        substack_id = f"gmail_{email_data['id']}"

        existing = self.db.articles.find_one({'substack_id': substack_id})

        if existing:
            if existing.get('deleted'):
                # Check if we should restore deleted articles
                import sys
                restore_deleted = '--restore-deleted' in sys.argv

                if restore_deleted:
                    print(f"  🔄 Restoring deleted article: {article_data.get('title', 'Untitled')}")
                    update_fields = {
                        'deleted': False,
                        'content_markdown': article_data.get('content_markdown'),
                        'content_html': article_data.get('content_html'),
                        'preview': article_data.get('preview'),
                        'word_count': article_data.get('word_count'),
                        'reading_time_minutes': article_data.get('reading_time_minutes'),
                    }
                    if article_data.get('url'):
                        update_fields['url'] = article_data['url']
                    self.db.articles.update_one({'_id': existing['_id']}, {'$set': update_fields})
                    existing.update(update_fields)
                    return existing
                else:
                    print(f"Article was deleted by user, skipping: {article_data.get('title', 'Untitled')}")
                    return None
            print(f"Article already exists: {article_data.get('title', 'Untitled')}")
            # Update the article if it has no content but we now have content
            if (not existing.get('content_markdown') or existing.get('word_count', 0) == 0) and article_data.get('content_markdown'):
                print(f"  📝 Updating empty article with new content ({article_data.get('word_count', 0)} words)")
                update_fields = {
                    'content_markdown': article_data.get('content_markdown'),
                    'content_html': article_data.get('content_html'),
                    'preview': article_data.get('preview'),
                    'word_count': article_data.get('word_count', 0),
                    'reading_time_minutes': article_data.get('reading_time_minutes', 1),
                }
                if article_data.get('url'):
                    update_fields['url'] = article_data['url']
                self.db.articles.update_one({'_id': existing['_id']}, {'$set': update_fields})
            return existing

        # Create new article
        # For forwarded emails, always use the email subject as title
        article_title = article_data.get('title')
        if not article_title or article_title in ['Untitled', 'Forwarded Newsletter', 'Use Email Subject']:
            # Use email subject, cleaning up any forward prefixes
            subject = email_data['subject']
            # Remove common forward prefixes
            for prefix in ['Fwd: ', 'FW: ', 'Re: ', 'RE: ']:
                if subject.startswith(prefix):
                    subject = subject[len(prefix):]
            article_title = subject if subject else 'Untitled'

        # Clean footer from HTML content too
        content_html = article_data.get('content_html')
        if content_html:
            content_html = remove_substack_footer(content_html)

        article_doc = {
            'substack_id': substack_id,
            'title': article_title,
            'subtitle': article_data.get('subtitle'),
            'url': article_data.get('url'),
            'content_html': content_html,
            'content_markdown': article_data.get('content_markdown'),
            'preview': article_data.get('preview'),
            'word_count': article_data.get('word_count', 0),
            'reading_time_minutes': article_data.get('reading_time_minutes', 1),
            'author_id': author['_id'],
            'author_name': author['name'],
            'published_at': email_data['date'],
            'collected_at': datetime.now(timezone.utc),
            'created_at': datetime.now(timezone.utc),
            'source': 'email',
            'deleted': False,
        }

        result = self.db.articles.insert_one(article_doc)
        article_doc['_id'] = result.inserted_id
        return article_doc

    def collect_newsletters(self, query: str = None, max_results: int = 50) -> int:
        """Main collection method"""
        print(f"🔍 Searching for Substack newsletters...")

        try:
            # Authenticate if needed
            if not self.service:
                print("📧 Authenticating with Gmail...")
                self.authenticate()

            # Search for emails - use expanded query if none provided
            if query is None:
                # Include emails from your UniSG account that contain Substack forwards
                # For forwarded emails, we search by sender and content, not subject

                # Load forwarded authors from config for comprehensive search
                config_path = Path(__file__).parent.parent.parent / 'forwarded_authors.json'
                author_emails = []

                if config_path.exists():
                    try:
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                            author_emails = [
                                f'"{author["email"]}"'
                                for author in config.get('forwarded_authors', [])
                            ]
                    except Exception:
                        pass  # Silently fall back to basic search

                # Build comprehensive query - be more specific for forwarded emails
                query_parts = [
                    'from:substack.com',
                    '(from:siegfried.handschuh@unisg.ch AND substack)',
                    '(from:me to:me AND substack)',
                    '"@substack.com"'
                ]
                query_parts.extend(author_emails)

                query = ' OR '.join(query_parts)

            message_ids = self.search_substack_emails(query, max_results)
            print(f"📬 Found {len(message_ids)} Substack emails")

            # Process each email
            articles_saved = 0
            for i, msg_id in enumerate(message_ids, 1):
                print(f"\n📖 Processing email {i}/{len(message_ids)}...")

                # Get email content
                email_data = self.get_email_content(msg_id)
                if not email_data:
                    continue

                # Save to database
                article = self.save_article(email_data)
                if article:
                    articles_saved += 1
                    title = article.get('title', 'Untitled')
                    print(f"  ✅ Saved: {title[:60]}...")

            print(f"\n✅ Collection complete! Saved {articles_saved} new articles")
            return articles_saved

        except Exception as e:
            print(f"❌ Error during collection: {e}")
            raise

# Helper function for command-line usage
def main():
    """Run the collector from command line"""
    import argparse

    parser = argparse.ArgumentParser(description='Collect Substack newsletters from Gmail')
    parser.add_argument('--query', default=None,
                       help='Gmail search query (default: comprehensive search)')
    parser.add_argument('--max', type=int, default=50,
                       help='Maximum emails to process (default: 50)')
    parser.add_argument('--setup', action='store_true',
                       help='Run initial Gmail authentication setup')
    parser.add_argument('--forwarded', action='store_true',
                       help='Search only for forwarded emails from configured authors')
    parser.add_argument('--after', default=None,
                       help='Collect emails after this date (format: YYYY-MM-DD, e.g., 2025-08-11)')
    parser.add_argument('--before', default=None,
                       help='Collect emails before this date (format: YYYY-MM-DD, e.g., 2025-08-12)')
    parser.add_argument('--on', default=None,
                       help='Collect emails on this specific date (format: YYYY-MM-DD, e.g., 2025-08-11)')
    parser.add_argument('--days', type=int, default=None,
                       help='Collect emails from the last N days (e.g., --days 2 for last 2 days)')
    parser.add_argument('--restore-deleted', action='store_true',
                       help='Restore and re-import soft-deleted articles (undelete them)')

    args = parser.parse_args()

    collector = GmailSubstackCollector()

    if args.setup:
        print("🔐 Setting up Gmail authentication...")
        print("This will open a browser window for you to authorize access.")
        collector.authenticate()
        print("✅ Authentication successful! Token saved.")
    else:
        # Build query based on flags
        query_parts = []

        # Add date filters if specified
        from datetime import datetime, timedelta

        if args.days:
            # Calculate date range from --days parameter
            today = datetime.now(timezone.utc)
            days_ago = (today - timedelta(days=args.days)).strftime('%Y-%m-%d')
            query_parts.append(f'after:{days_ago}')
            print(f"📅 Collecting emails from the last {args.days} days (since {days_ago})")
        elif args.on:
            # Specific date - use after and before to bracket the day
            query_parts.append(f'after:{args.on}')
            # Add one day for before (Gmail date logic)
            date_obj = datetime.strptime(args.on, '%Y-%m-%d')
            next_day = (date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
            query_parts.append(f'before:{next_day}')
            print(f"📅 Collecting emails from {args.on}")
        else:
            if args.after:
                query_parts.append(f'after:{args.after}')
                print(f"📅 Collecting emails after {args.after}")
            if args.before:
                query_parts.append(f'before:{args.before}')
                print(f"📅 Collecting emails before {args.before}")

        # Build base query
        if args.query:
            base_query = args.query
        elif args.forwarded:
            # Search only for forwarded emails from configured authors
            print("🔄 Searching only for forwarded emails from configured authors...")

            # Load forwarded authors from config
            config_path = Path(__file__).parent.parent.parent / 'forwarded_authors.json'
            author_emails = []

            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        author_emails = [
                            f'"{author["email"]}"'
                            for author in config.get('forwarded_authors', [])
                        ]
                        print(f"Loaded {len(author_emails)} configured authors")
                except Exception as e:
                    print(f"Warning: Could not load forwarded_authors.json: {e}")
            else:
                print("Warning: forwarded_authors.json not found")

            # Build query with dynamic author emails - be very specific for forwarded emails
            # Only search for forwarded emails that contain the actual configured author names/emails
            forward_query_parts = []

            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        for author in config.get('forwarded_authors', []):
                            # Search for forwarded emails that contain this specific author's name or email
                            forward_query_parts.extend([
                                f'(from:siegfried.handschuh@unisg.ch AND "{author["name"]}")',
                                f'(from:siegfried.handschuh@unisg.ch AND "{author["email"]}")',
                                f'(from:me to:me AND "{author["name"]}")',
                                f'(from:me to:me AND "{author["email"]}")'
                            ])
                except Exception:
                    pass

            # Combine forwarded query parts
            forwarded_base = ' OR '.join(forward_query_parts + author_emails)
            base_query = f'({forwarded_base})'
        else:
            # Default comprehensive Substack search
            base_query = 'from:substack OR from:@substack.com'

        # Combine base query with date filters
        if query_parts:  # Has date filters
            date_filters = ' '.join(query_parts)
            query = f'{base_query} {date_filters}'
        else:
            query = base_query

        print(f"📧 Final query: {query[:100]}...")

        articles = collector.collect_newsletters(query, args.max)

        # Show summary
        db = get_database()
        total_articles = db.articles.count_documents({})
        total_authors = db.substack_authors.count_documents({})

        print(f"\n📊 Database Summary:")
        print(f"  Total articles: {total_articles}")
        print(f"  Total authors: {total_authors}")

if __name__ == "__main__":
    main()
