#!/usr/bin/env python3
"""
Test the actual import with real cookies
"""
import requests
import json
from app.services.curl_parser import parse_curl_command

# Your actual cURL command
curl_command = """curl 'https://magazine.sebastianraschka.com/p/understanding-and-coding-self-attention' \
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
  -H 'accept-language: en-GB,en;q=0.9,en-US;q=0.8,de-CH;q=0.7,de-DE;q=0.6,de;q=0.5' \
  -H 'cache-control: max-age=0' \
  -b 'cookie_storage_key=8b64c9e4-30c2-40df-bcf5-c1f061793691; connect.sid=s%3A-lfX3qmFqQQi1g-_4H7uZL-TeU6n7Pq2.zPWnyQdrNeR1s2b8G2TyZbXGcdTZlFenvqVahXeV4Bw; __stripe_mid=7daab6a0-beb4-4237-8995-a9abe90921a9705b06; ajs_anonymous_id=%222f15c9e5f19c0f17c045398fffa0f9cc%22; ab_testing_id=%22or-77dfe3be-ec64-4a2a-b73d-b63bc4410a63%22; _ga=GA1.1.594497823.1754906542; _gcl_au=1.1.1145384482.1754906542; ab_experiment_sampled=%22false%22; hideCookieBanner=true; muxData=mux_viewer_id=8f3426a5-28d1-4888-86b5-3798c8386519&msn=0.9919217162130639&sid=eecbc93d-c335-45f0-9c1d-9269d5586b0a&sst=1755273301541&sex=1755275226690; __cf_bm=PK.75EPtbL26Y1Xs1twT.1kDkRTrVtgpmSgF_65Dsz4-1755274571-1.0.1.1-nm67cC3JRC8m6n6pGBDGVeN50jOmtIm9IWv8yxbeFg4Ufn41bTte_WM2rfV1uWy6w4ugYyQvurL.N2r5vzNMYeenZXHYFf15lufvEgMb6PI; __stripe_sid=47ce9692-6432-4fae-b2f7-31e513ae373a874e1f; visit_id=%7B%22id%22%3A%22039f8263-1e4e-4edb-b522-bfee2b173c2d%22%2C%22timestamp%22%3A%222025-08-15T16%3A27%3A15.249Z%22%7D; _ga_Z4BJTTV5MZ=GS2.1.s1755269622$o7$g1$t1755275254$j26$l0$h0; AWSALBTG=QNJVfYqf2dr11g9V2mzsPZxtSbIhM3osg5DhyqYpNuenWBDZVHsnpldrURwIryxAnd2GHtJqan1RubHrgpyk+JGmlN6bvaJhYhxCIb10AmH55r4dBVnkCPs/TioyAodjkOiw9LfT+yK892Tkl6RP5mzruJu1QY9sPlqbx+96lUuw; AWSALBTGCORS=QNJVfYqf2dr11g9V2mzsPZxtSbIhM3osg5DhyqYpNuenWBDZVHsnpldrURwIryxAnd2GHtJqan1RubHrgpyk+JGmlN6bvaJhYhxCIb10AmH55r4dBVnkCPs/TioyAodjkOiw9LfT+yK892Tkl6RP5mzruJu1QY9sPlqbx+96lUuw; _dd_s=rum=0&expire=1755276161912' \
  -H 'priority: u=0, i' \
  -H 'referer: http://localhost:3000/' \
  -H 'sec-ch-ua: "Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: document' \
  -H 'sec-fetch-mode: navigate' \
  -H 'sec-fetch-site: same-origin' \
  -H 'sec-fetch-user: ?1' \
  -H 'upgrade-insecure-requests: 1' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0'"""

print("Testing direct fetch with your cookies...")
print("=" * 60)

# Parse the cURL command
url, cookies, headers = parse_curl_command(curl_command)

print(f"URL: {url}")
print(f"Found {len(cookies)} cookies")
print(f"Cookie keys: {list(cookies.keys())[:5]}")

# Try to fetch directly
print("\nAttempting to fetch article...")
session = requests.Session()
session.cookies.update(cookies)
session.headers.update({
    'User-Agent': headers.get('user-agent', 'Mozilla/5.0')
})

try:
    response = session.get(url, timeout=10)
    print(f"Response status: {response.status_code}")
    print(f"Response length: {len(response.text)} characters")
    
    # Check if it looks like we got the full article
    if "This post is for paid subscribers" in response.text:
        print("❌ Got paywall message - cookies might be expired")
    elif len(response.text) > 50000:
        print("✅ Got full article content!")
    else:
        print("⚠️ Got some content, but might be truncated")
        
    # Save response for inspection
    with open('test_response.html', 'w') as f:
        f.write(response.text)
    print("\nResponse saved to test_response.html")
    
except requests.Timeout:
    print("❌ Request timed out after 10 seconds")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nTesting API endpoint...")
print("=" * 60)

# Test the API endpoint
api_url = "http://localhost:8000/api/v2/articles/enhanced/import-with-cookies"
payload = {
    "url": url,
    "curl_command": curl_command
}

try:
    api_response = requests.post(api_url, json=payload, timeout=60)
    print(f"API Response status: {api_response.status_code}")
    result = api_response.json()
    print(f"API Result: {json.dumps(result, indent=2)}")
except requests.Timeout:
    print("❌ API request timed out after 60 seconds")
except Exception as e:
    print(f"❌ API Error: {e}")