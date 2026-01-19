#!/usr/bin/env python3
"""
Debug what content is available when authenticated
"""

import requests
from bs4 import BeautifulSoup

def debug_authenticated_content(login_link: str, article_url: str):
    """See what content selectors are available when authenticated"""
    
    print("=" * 60)
    print("Debugging Authenticated Content")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # Authenticate
    print("🔐 Authenticating...")
    response = session.get(login_link, allow_redirects=True)
    print(f"Auth response: {response.status_code}")
    
    # Fetch the article
    print(f"\n📥 Fetching article: {article_url}")
    response = session.get(article_url)
    print(f"Article response: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check various content selectors
    selectors_to_check = [
        'div.available-content',
        'div.body.markup',
        'div.post-content',
        'div[class*="post-content"]',
        'div.portable-text-block',
        'article.post',
        'div.post',
        'main',
        'article',
        'div[class*="body"]',
        'div[class*="content"]'
    ]
    
    print("\n📋 Content Selectors Found:")
    print("-" * 40)
    
    for selector in selectors_to_check:
        elem = soup.select_one(selector)
        if elem:
            text_length = len(elem.get_text(strip=True))
            # Count certain indicators
            num_headers = len(elem.find_all(['h1', 'h2', 'h3', 'h4']))
            num_paragraphs = len(elem.find_all('p'))
            num_links = len(elem.find_all('a'))
            
            print(f"\n✅ {selector}")
            print(f"   Text length: {text_length:,} chars")
            print(f"   Headers: {num_headers}, Paragraphs: {num_paragraphs}, Links: {num_links}")
            
            # Check if it seems complete
            text = elem.get_text(strip=True).lower()
            if 'references' in text[-1000:] or 'bibliography' in text[-1000:]:
                print(f"   📚 Contains references section (likely complete)")
            if 'thanks for reading' in text[-1000:] or 'subscribe' in text[-1000:]:
                print(f"   📝 Contains footer content (likely complete)")
        else:
            print(f"❌ {selector} - Not found")
    
    # Check for paywall indicators
    print("\n🔒 Paywall Check:")
    paywall_selectors = [
        '.paywall',
        '.subscription-widget',
        '.subscribe-prompt',
        '.upgrade-prompt',
        'button[class*="subscribe"]'
    ]
    
    paywall_found = False
    for selector in paywall_selectors:
        elem = soup.select_one(selector)
        if elem:
            print(f"⚠️ Paywall element found: {selector}")
            paywall_found = True
    
    if not paywall_found:
        print("✅ No paywall elements detected")
    
    # Find the longest content element
    print("\n🏆 Longest Content Element:")
    longest_elem = None
    longest_length = 0
    longest_selector = None
    
    for selector in selectors_to_check:
        elem = soup.select_one(selector)
        if elem:
            text_length = len(elem.get_text(strip=True))
            if text_length > longest_length:
                longest_length = text_length
                longest_elem = elem
                longest_selector = selector
    
    if longest_elem:
        print(f"Selector: {longest_selector}")
        print(f"Length: {longest_length:,} characters")
        
        # Show the last part
        text = longest_elem.get_text(strip=True)
        print(f"\nLast 500 characters of best content:")
        print("-" * 40)
        print(text[-500:])
        print("-" * 40)
    
    # Save the full HTML for inspection
    with open('debug_article.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print(f"\n💾 Full HTML saved to debug_article.html for inspection")


if __name__ == "__main__":
    login_link = "https://email.mg-tx1.substack.com/c/eJxMkslyozAQhp9G3EyhZgsHDoxjyrhilEXG9lxcQhIg9gBe4Omn4ppDzt1fdf8LZ5PMu2H26y5XrSZ8w0klA0362LVtcLHleZpsmKovuWzlwCYpLmz6NXUtTyt8jrPUzVzMMtfAFjBpcYPZIssYvGS2aWvKBwNs4wXb2AbL9nRTT7GXmh63MgsszLGnO4N1E_VSIcto8tX0wPp4TceJ8UrnXaOp8ZIN8vmMPw1XqdV-MU39iMwAQYgg_L2NIGS9QhDeMILwCa2eGhGEvGv6Wk4SmeHUVbJF5qucd5hDMp-grqKye-yXwIzLDSY0H6M2rrkZ9ynYu7_ryIlKQY5tMX0loZMceya2xXe8FRVdYiJbYSSn3fi5FcWhSW6Ruit2ChRR0XymwUzKzbyngUNoNBPa12caPEhzeJzh7OzhszgvHY5hfydlUhDK1dt6159PH4qUGzOmhzleNgah1Rg1icXXkbOnHMc0MmMa2OTr51a8RGWn-DZRbzT44RdxjBRRuzEF0adq5-lZufoj7-9KjZ_Uedt7t0NdvB-heVjz-uJ-r2h2vF6Kjw83rRA4gxRqkHxC5isCG8Kia6Q2-KOSeTYoKfSCtWLkxbVAlpH_GP1Ma7ymomuYav37_a5N_wt2HeVwUcLHpuE62PZetJsP_wIAAP__ZzTUJg"
    article_url = "https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one"
    
    debug_authenticated_content(login_link, article_url)