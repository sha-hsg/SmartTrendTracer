"""
Selective Gmail Substack Collector
Only collects emails from specific authors defined in forwarded_authors.json
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import get_db, SubstackArticle, SubstackAuthor

class SelectiveGmailCollector(GmailSubstackCollector):
    """Collector that only processes emails from specific authors"""
    
    def __init__(self, db_session=None):
        super().__init__(db_session)
        self.config = self._load_config()
        self.allowed_authors = {
            author['email'].lower(): author 
            for author in self.config.get('forwarded_authors', [])
        }
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        config_path = Path(__file__).parent.parent.parent / 'forwarded_authors.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {'forwarded_authors': [], 'forward_settings': {}}
    
    def _should_collect_email(self, email_data: Dict) -> bool:
        """Check if email should be collected based on author"""
        if not email_data:
            return False
        
        # Always collect direct Substack emails
        sender = email_data.get('sender', '').lower()
        if '@substack.com' in sender:
            return True
        
        # Check if forwarding is enabled
        settings = self.config.get('forward_settings', {})
        if not settings.get('enabled', True):
            return False
        
        # Check if it's a forwarded email
        from_email = settings.get('from_email', '')
        if from_email and from_email.lower() not in sender.lower():
            # Not from the configured forward source
            return False
        
        # Check email body for allowed authors
        html_body = email_data.get('html_body', '')
        if html_body:
            body_lower = html_body.lower()
            
            # Check each allowed author
            for author_email, author_info in self.allowed_authors.items():
                # Check if any search pattern matches
                for pattern in author_info.get('search_patterns', []):
                    if pattern.lower() in body_lower:
                        print(f"  ✅ Found allowed author: {author_info['name']}")
                        return True
        
        return False
    
    def _extract_author_from_forward(self, email_data: Dict) -> Optional[Dict]:
        """Extract author info from forwarded email"""
        html_body = email_data.get('html_body', '')
        if not html_body:
            return None
        
        # Check for each configured author
        for author_email, author_info in self.allowed_authors.items():
            # Check if this author's patterns are in the email
            body_lower = html_body.lower()
            for pattern in author_info.get('search_patterns', []):
                if pattern.lower() in body_lower:
                    # Found this author - return their info
                    return {
                        'name': author_info['name'],
                        'subdomain': author_email.split('@')[0],
                        'email': author_email,
                        'newsletter': author_info.get('newsletter', '')
                    }
        
        return None
    
    def get_email_content(self, msg_id: str) -> Dict:
        """Override to filter emails"""
        email_data = super().get_email_content(msg_id)
        
        if not email_data:
            return None
        
        # Check if we should collect this email
        if not self._should_collect_email(email_data):
            print(f"  ⏭️ Skipping email (not from allowed authors)")
            return None
        
        # If it's a forwarded email, enhance author info
        if 'unisg.ch' in email_data.get('sender', '').lower():
            author_info = self._extract_author_from_forward(email_data)
            if author_info:
                email_data['author'] = author_info
        
        return email_data
    
    def collect_selective(self, max_results: int = 100) -> int:
        """Collect only emails from configured authors"""
        print("📧 Selective Substack Collection")
        print(f"Configured authors: {', '.join([a['name'] for a in self.config.get('forwarded_authors', [])])}")
        print()
        
        # Build search query
        queries = []
        
        # Direct Substack emails
        queries.append('from:substack.com')
        
        # Forwarded emails
        settings = self.config.get('forward_settings', {})
        if settings.get('enabled') and settings.get('from_email'):
            from_email = settings['from_email']
            # Search for forwarded emails
            queries.append(f'from:{from_email}')
            
            # Add specific search terms for each author
            for author in self.config.get('forwarded_authors', []):
                for pattern in author.get('search_patterns', []):
                    queries.append(f'"{pattern}"')
        
        # Combine queries with OR
        full_query = ' OR '.join(set(queries))  # Remove duplicates
        
        print(f"Search query: {full_query[:100]}...")
        return self.collect_newsletters(query=full_query, max_results=max_results)

def main():
    """Run selective collection"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect Substack from specific authors only')
    parser.add_argument('--max', type=int, default=100, help='Max emails to process')
    parser.add_argument('--show-config', action='store_true', help='Show configuration')
    
    args = parser.parse_args()
    
    collector = SelectiveGmailCollector()
    
    if args.show_config:
        print("📋 Configuration:")
        print(json.dumps(collector.config, indent=2))
        return
    
    # Run collection
    articles = collector.collect_selective(args.max)
    
    # Show results
    db = next(get_db())
    
    print("\n📊 Collection Results:")
    print(f"New articles collected: {articles}")
    
    # Show articles by author
    authors = db.query(
        SubstackAuthor.name,
        SubstackAuthor.subdomain,
        SubstackAuthor.email
    ).distinct().all()
    
    print("\n👥 Authors in database:")
    for name, subdomain, email in authors:
        if any(email == a['email'] for a in collector.config.get('forwarded_authors', [])):
            # This is one of our configured authors
            count = db.query(SubstackArticle).join(SubstackAuthor).filter(
                SubstackAuthor.email == email,
                SubstackArticle.deleted == False
            ).count()
            print(f"  ✅ {name}: {count} articles [{subdomain}]")
        elif '@substack.com' in (email or ''):
            # Other Substack author
            count = db.query(SubstackArticle).join(SubstackAuthor).filter(
                SubstackAuthor.email == email,
                SubstackArticle.deleted == False
            ).count()
            print(f"  📧 {name}: {count} articles")

if __name__ == "__main__":
    main()