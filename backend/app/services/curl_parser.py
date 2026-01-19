"""
cURL command parser for extracting cookies and headers
"""
import re
import shlex
from typing import Dict, Optional, Tuple

def parse_curl_command(curl_command: str) -> Tuple[Optional[str], Dict[str, str], Dict[str, str]]:
    """
    Parse a cURL command to extract URL, cookies, and headers
    
    Returns:
        Tuple of (url, cookies_dict, headers_dict)
    """
    
    # Clean up the command (remove backslashes and newlines)
    curl_command = curl_command.replace('\\\n', ' ').replace('\\', '')
    
    # Try to extract URL (usually the first quoted string after 'curl')
    url_match = re.search(r"curl\s+['\"]([^'\"]+)['\"]", curl_command)
    if not url_match:
        # Try without quotes
        url_match = re.search(r"curl\s+(\S+)", curl_command)
    
    url = url_match.group(1) if url_match else None
    
    cookies = {}
    headers = {}
    
    # Method 1: Try to parse with shlex (handles quotes properly)
    try:
        # Split the command into tokens
        tokens = shlex.split(curl_command)
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Look for -b or --cookie flag (cookie data)
            if token in ['-b', '--cookie'] and i + 1 < len(tokens):
                cookie_value = tokens[i + 1]
                # Parse cookies from -b flag
                for cookie_pair in cookie_value.split(';'):
                    cookie_pair = cookie_pair.strip()
                    if '=' in cookie_pair:
                        key, val = cookie_pair.split('=', 1)
                        cookies[key.strip()] = val.strip()
                i += 2
            # Look for -H or --header
            elif token in ['-H', '--header'] and i + 1 < len(tokens):
                header_value = tokens[i + 1]
                
                # Parse header (format: "Name: Value")
                if ':' in header_value:
                    name, value = header_value.split(':', 1)
                    name = name.strip()
                    value = value.strip()
                    
                    headers[name.lower()] = value
                    
                    # If it's a cookie header, parse the cookies
                    if name.lower() == 'cookie':
                        for cookie_pair in value.split(';'):
                            cookie_pair = cookie_pair.strip()
                            if '=' in cookie_pair:
                                key, val = cookie_pair.split('=', 1)
                                cookies[key.strip()] = val.strip()
                
                i += 2
            else:
                i += 1
                
    except Exception as e:
        print(f"Shlex parsing failed: {e}, trying regex method")
        
        # Method 2: Fallback to regex parsing
        # Look for -b flag for cookies
        cookie_patterns = [
            r"-b\s+['\"]([^'\"]+)['\"]",
            r"--cookie\s+['\"]([^'\"]+)['\"]",
            r"-b\s+'([^']+)'",
            r'-b\s+"([^"]+)"',
            r"-b\s+(\S+)",  # No quotes
        ]
        
        for pattern in cookie_patterns:
            match = re.search(pattern, curl_command)
            if match:
                cookie_string = match.group(1)
                for cookie_pair in cookie_string.split(';'):
                    cookie_pair = cookie_pair.strip()
                    if '=' in cookie_pair:
                        key, val = cookie_pair.split('=', 1)
                        cookies[key.strip()] = val.strip()
                break
        
        # Look for all -H "header: value" patterns
        header_patterns = [
            r"-H\s+['\"]([^:]+):\s*([^'\"]+)['\"]",
            r"--header\s+['\"]([^:]+):\s*([^'\"]+)['\"]",
            r"-H\s+'([^:]+):\s*([^']+)'",
            r'-H\s+"([^:]+):\s*([^"]+)"',
        ]
        
        for pattern in header_patterns:
            for match in re.finditer(pattern, curl_command, re.IGNORECASE):
                name = match.group(1).strip()
                value = match.group(2).strip()
                headers[name.lower()] = value
                
                # If it's a cookie header, parse the cookies
                if name.lower() == 'cookie':
                    for cookie_pair in value.split(';'):
                        cookie_pair = cookie_pair.strip()
                        if '=' in cookie_pair:
                            key, val = cookie_pair.split('=', 1)
                            cookies[key.strip()] = val.strip()
    
    return url, cookies, headers

def extract_cookies_from_curl(curl_command: str) -> Optional[Dict[str, str]]:
    """
    Simple function to extract just cookies from a cURL command
    """
    _, cookies, _ = parse_curl_command(curl_command)
    return cookies if cookies else None