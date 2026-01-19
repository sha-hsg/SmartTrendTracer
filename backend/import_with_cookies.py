#!/usr/bin/env python3
"""
Import article using browser cookies
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from app.models import get_db
from app.models.substack import SubstackArticle
from app.services.url_article_importer import URLArticleImporter


# Your cookies from the cURL command
COOKIES = {
    'cookie_storage_key': 'd83cec84-23da-4f94-bf73-e5c4d381caa9',
    '_ga': 'GA1.1.82721998.1755272247',
    '__cf_bm': 'I6C0vvtqrjwPBRpr2J4NaCOryXziow8dudSNChba6f0-1755272251-1.0.1.1-FKHR1g95M8QHXztV8Rd.Jp4VjRD6BUcRFiOV0m0lpti0wIp4VBhbtDHfeVl27w.GlC4y5mL3TmN4PLtAvDbZ8k4Iy9nBQ0tYf2CVRadqZ3I',
    'disable_html_pixels': '1',
    'disable_experiments': '1',
    'connect.sid': 's%3AkSKHV5VA8pk-txZIn1NKg_HNYb60Dfru.OlM%2FHOpUi8vu4EKUzzEMi3uMHhEdFhfKjqc7dgpPIsg',
    'ajs_anonymous_id': '%222f15c9e5f19c0f17c045398fffa0f9cc%22',
    'ab_testing_id': '%22or-e5f8dba1-6eba-4e03-9dc8-dc2c2ea0e4be%22',
    'hideCookieBanner': 'true',
    '_gcl_au': '1.1.848438828.1755272254',
    '_ga_BYQXBRPK81': 'GS2.1.s1755272247$o1$g1$t1755272276$j31$l0$h0',
    'visit_id': '%7B%22id%22%3A%22cc15391a-4743-469a-94c9-e34031a29011%22%2C%22timestamp%22%3A%222025-08-15T15%3A39%3A13.301Z%22%7D',
    '_ga_Z4BJTTV5MZ': 'GS2.1.s1755272253$o1$g1$t1755272708$j26$l0$h0',
    'AWSALBTG': 'Kck6rNrY1tdPXpsVJvl9m9bi2YWd2DI/pvx+e9XKPncZdXG6FMUijNVkO0CYJ3whUkB7tGXbE+3UtoPleHVEcoYTrHcLTRI2veh7b9m5UWfG3qnh/Hc+d9PuyBnAcY5GAOtmKUTtji2EVqaCOO7DhPl1Te1zJCP6/71YIazg8ACn',
    'AWSALBTGCORS': 'Kck6rNrY1tdPXpsVJvl9m9bi2YWd2DI/pvx+e9XKPncZdXG6FMUijNVkO0CYJ3whUkB7tGXbE+3UtoPleHVEcoYTrHcLTRI2veh7b9m5UWfG3qnh/Hc+d9PuyBnAcY5GAOtmKUTtji2EVqaCOO7DhPl1Te1zJCP6/71YIazg8ACn',
    '_dd_s': 'rum=0&expire=1755273622109'
}

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,de;q=0.7',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
}

def import_with_session():
    """Import article using authenticated browser session"""
    
    print("=" * 60)
    print("Importing with Browser Session Cookies")
    print("=" * 60)
    
    article_url = "https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one"
    
    # Create session with cookies
    session = requests.Session()
    session.cookies.update(COOKIES)
    session.headers.update(HEADERS)
    
    print(f"📥 Fetching article with authenticated session...")
    response = session.get(article_url)
    
    if response.status_code == 200:
        print(f"✅ Successfully fetched article")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for paywall
        paywall = soup.select_one('.paywall')
        if paywall:
            print("⚠️ Paywall element still present, checking content...")
        else:
            print("✅ No paywall detected!")
        
        # Find the main content - try multiple selectors
        content_selectors = [
            'div.body.markup',
            'div.available-content',
            'article.post div.body',
            'div[class*="body"][class*="markup"]'
        ]
        
        content_elem = None
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                text_length = len(elem.get_text(strip=True))
                print(f"📏 Found content with selector '{selector}': {text_length:,} characters")
                if text_length > 10000:  # Substantial content
                    content_elem = elem
                    break
        
        if content_elem:
            # Save raw HTML for inspection
            with open('full_article.html', 'w', encoding='utf-8') as f:
                f.write(str(content_elem))
            print("💾 Raw HTML saved to full_article.html")
            
            # Process and import
            db = next(get_db())
            
            try:
                # Delete old truncated version
                old_article = db.query(SubstackArticle).filter_by(url=article_url).first()
                if old_article:
                    print(f"\n🗑️ Removing old version (ID: {old_article.id}, {old_article.word_count} words)")
                    old_word_count = old_article.word_count
                    old_char_count = len(old_article.content_markdown)
                    db.delete(old_article)
                    db.commit()
                else:
                    old_word_count = 0
                    old_char_count = 0
                
                # Process content
                importer = URLArticleImporter(db)
                
                # Clean HTML while preserving structure
                cleaned_html = importer._clean_article_content(str(content_elem))
                
                # Convert to markdown
                markdown_content = importer._html_to_markdown(cleaned_html)
                
                # Clean footers
                markdown_content = importer._clean_markdown_footers(markdown_content)
                
                # Create author
                author = importer._get_or_create_author({
                    'name': 'Sebastian Raschka, PhD',
                    'subdomain': 'magazine.sebastianraschka',
                    'url': 'https://magazine.sebastianraschka.com'
                })
                
                # Create article
                article = SubstackArticle(
                    author_id=author.id,
                    title="LLM Research Papers: The 2025 List (January to June)",
                    subtitle="The latest in LLM research with a hand-curated, topic-organized list of over 200 research papers from 2025",
                    substack_id=f"full_import_{datetime.now().isoformat()}",
                    slug="llm-research-papers-2025-list-one",
                    url=article_url,
                    content_html=cleaned_html,
                    content_markdown=markdown_content,
                    preview=importer._generate_preview(markdown_content),
                    published_at=datetime(2025, 7, 1),
                    word_count=len(markdown_content.split()),
                    reading_time_minutes=max(1, len(markdown_content.split()) // 200),
                    processed=True,
                    deleted=False
                )
                
                db.add(article)
                db.commit()
                
                print(f"\n✅ Successfully imported full article!")
                print(f"📄 Title: {article.title}")
                print(f"✍️ Author: {author.name}")
                print(f"📊 Word Count: {article.word_count:,} words")
                print(f"📏 Content Length: {len(markdown_content):,} characters")
                
                if old_word_count > 0:
                    word_increase = ((article.word_count - old_word_count) / old_word_count) * 100
                    char_increase = ((len(markdown_content) - old_char_count) / old_char_count) * 100
                    print(f"📈 Word Increase: +{word_increase:.1f}% ({article.word_count - old_word_count:,} more words)")
                    print(f"📈 Character Increase: +{char_increase:.1f}% ({len(markdown_content) - old_char_count:,} more chars)")
                
                print(f"🆔 Article ID: {article.id}")
                
                # Show beginning and end
                print(f"\n📝 Article beginning (first 500 chars):")
                print("-" * 40)
                print(markdown_content[:500])
                print("-" * 40)
                
                print(f"\n📝 Article ending (last 500 chars):")
                print("-" * 40)
                print(markdown_content[-500:])
                print("-" * 40)
                
                # Check for completeness indicators
                completeness_checks = []
                
                if 'references' in markdown_content.lower()[-5000:]:
                    completeness_checks.append("✅ References section found")
                
                if 'conclusion' in markdown_content.lower()[-5000:]:
                    completeness_checks.append("✅ Conclusion section found")
                    
                if len(markdown_content) > 50000:
                    completeness_checks.append("✅ Very long content (>50k chars)")
                    
                if '7.' in markdown_content or '7)' in markdown_content:
                    completeness_checks.append("✅ Contains section 7 (all categories)")
                
                if completeness_checks:
                    print("\n✨ Article Completeness Indicators:")
                    for check in completeness_checks:
                        print(f"   {check}")
                else:
                    print("\n⚠️ Could not verify completeness - please check manually")
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
                db.rollback()
            finally:
                db.close()
        else:
            print("❌ Could not find substantial content element")
            print("Saving full page for inspection...")
            with open('full_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("💾 Full page saved to full_page.html")
    else:
        print(f"❌ Failed to fetch article: {response.status_code}")


if __name__ == "__main__":
    import_with_session()