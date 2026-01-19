#!/usr/bin/env python3
"""
Test cURL command parsing for debugging
"""
import re

def parse_curl_cookies(curl_command):
    """Test function to parse cookies from cURL command"""
    
    print("Testing cURL command parsing...")
    print(f"Command length: {len(curl_command)} characters")
    print(f"First 100 chars: {curl_command[:100]}...")
    
    # Look for cookie header in cURL - try multiple patterns
    patterns = [
        r"-H\s+['\"]cookie:\s*([^'\"]+)['\"]",
        r"-H\s+['\"]Cookie:\s*([^'\"]+)['\"]",  # Capital C
        r"--cookie\s+['\"]([^'\"]+)['\"]",
        r"-H\s+'cookie:\s*([^']+)'",  # Single quotes
        r'-H\s+"cookie:\s*([^"]+)"',  # Double quotes
        r"-H\s+cookie:\s*([^\s]+)",   # No quotes
    ]
    
    for i, pattern in enumerate(patterns):
        print(f"\nTrying pattern {i+1}: {pattern}")
        match = re.search(pattern, curl_command, re.IGNORECASE)
        if match:
            print(f"✅ Match found!")
            cookie_string = match.group(1)
            print(f"Cookie string: {cookie_string[:100]}...")
            
            # Parse cookies
            cookies = {}
            for cookie in cookie_string.split('; '):
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    cookies[key] = value
            
            print(f"Parsed {len(cookies)} cookies")
            print(f"Cookie keys: {list(cookies.keys())[:5]}...")
            return cookies
    
    print("\n❌ No cookie header found in cURL command")
    
    # Check what headers ARE present
    header_pattern = r"-H\s+['\"]([^:]+):"
    headers = re.findall(header_pattern, curl_command)
    if headers:
        print(f"Found headers: {headers}")
    
    return None

# Test with sample cURL commands
test_commands = [
    # Standard format with double quotes
    '''curl 'https://example.com' -H "cookie: session_id=abc123; auth_token=xyz789"''',
    
    # Single quotes
    """curl 'https://example.com' -H 'cookie: session_id=abc123; auth_token=xyz789'""",
    
    # Capital Cookie
    '''curl 'https://example.com' -H "Cookie: session_id=abc123; auth_token=xyz789"''',
    
    # No quotes around header value
    '''curl 'https://example.com' -H cookie:session_id=abc123;auth_token=xyz789''',
    
    # Real browser format (what Chrome usually generates)
    """curl 'https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one' \\
  -H 'accept: text/html,application/xhtml+xml' \\
  -H 'cookie: substack.sid=abc123def456; substack.lli=1' \\
  -H 'user-agent: Mozilla/5.0'"""
]

if __name__ == "__main__":
    print("=" * 60)
    print("cURL Cookie Parser Test")
    print("=" * 60)
    
    for i, cmd in enumerate(test_commands, 1):
        print(f"\n\nTest {i}:")
        print("-" * 40)
        parse_curl_cookies(cmd)
    
    print("\n\n" + "=" * 60)
    print("Paste your actual cURL command below:")
    print("(Press Ctrl+D when done)")
    print("=" * 60)
    
    import sys
    user_curl = sys.stdin.read()
    if user_curl.strip():
        print("\n\nParsing your cURL command:")
        print("-" * 40)
        parse_curl_cookies(user_curl)