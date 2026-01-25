"""
Substack authentication service with magic link support
"""

import requests
import time
import json
from typing import Optional, Dict
from urllib.parse import urlparse, parse_qs


class SubstackAuthService:
    """Handle Substack authentication with magic link flow"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.email = None
        self.subdomain = None
        self._closed = False

    def close(self):
        """Explicitly close the session."""
        if not self._closed:
            self._closed = True
            self.session.close()

    def __del__(self):
        """Ensure session is closed when object is garbage collected."""
        try:
            if not self._closed:
                self.session.close()
        except Exception:
            pass  # Ignore errors during cleanup

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.close()
        return False
        
    def request_magic_link(self, email: str, subdomain: str = None) -> Dict:
        """
        Request a magic link to be sent to the email
        
        Args:
            email: Email address to send the magic link to
            subdomain: Specific Substack publication subdomain (optional)
            
        Returns:
            Dict with request status
        """
        self.email = email
        self.subdomain = subdomain
        
        try:
            # Different publications might have different login endpoints
            if subdomain:
                login_url = f"https://{subdomain}.substack.com/api/v1/login"
                referer = f"https://{subdomain}.substack.com"
            else:
                login_url = "https://substack.com/api/v1/login"
                referer = "https://substack.com"
            
            # Request magic link
            response = self.session.post(
                login_url,
                json={
                    "email": email,
                    "password": "",  # Empty password triggers magic link
                    "captcha_response": None
                },
                headers={
                    "Content-Type": "application/json",
                    "Origin": referer,
                    "Referer": f"{referer}/sign-in"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('type') == 'success':
                    return {
                        'success': True,
                        'message': f'Magic link sent to {email}. Please check your email and provide the verification link or code.'
                    }
            
            # Alternative: Try the account endpoint
            response = self.session.post(
                f"{referer}/api/v1/email-login",
                json={"email": email},
                headers={
                    "Content-Type": "application/json",
                    "Origin": referer,
                    "Referer": f"{referer}/account/login"
                }
            )
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'message': f'Login email sent to {email}. Please check your inbox for the magic link.'
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to send magic link: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error requesting magic link: {str(e)}'
            }
    
    def authenticate_with_token(self, token: str) -> bool:
        """
        Authenticate using the token from the magic link
        
        Args:
            token: Token extracted from the magic link
            
        Returns:
            True if authentication successful
        """
        try:
            if self.subdomain:
                auth_url = f"https://{self.subdomain}.substack.com/api/v1/email-login"
            else:
                auth_url = "https://substack.com/api/v1/email-login"
            
            # Use the token to authenticate
            response = self.session.get(
                auth_url,
                params={'token': token}
            )
            
            if response.status_code == 200:
                # Check if we're authenticated by trying to access account info
                account_response = self.session.get(
                    f"https://{self.subdomain or 'substack'}.substack.com/api/v1/user"
                )
                
                if account_response.status_code == 200:
                    print("✅ Successfully authenticated with Substack")
                    return True
                    
            return False
            
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def authenticate_with_link(self, magic_link: str) -> bool:
        """
        Authenticate using the full magic link URL
        
        Args:
            magic_link: The full URL from the email
            
        Returns:
            True if authentication successful
        """
        try:
            # Extract token from the magic link
            parsed = urlparse(magic_link)
            params = parse_qs(parsed.query)
            
            # Token might be in different parameters
            token = params.get('token', params.get('t', params.get('code', [None])))[0]
            
            if not token:
                # Sometimes the entire path contains the token
                if '/email-login' in magic_link:
                    # Follow the redirect
                    response = self.session.get(magic_link, allow_redirects=True)
                    
                    if response.status_code == 200:
                        # Check if we're logged in
                        if 'substack.sid' in self.session.cookies:
                            print("✅ Successfully authenticated via magic link")
                            return True
                else:
                    print("❌ Could not extract token from magic link")
                    return False
            
            return self.authenticate_with_token(token)
            
        except Exception as e:
            print(f"❌ Error processing magic link: {e}")
            return False
    
    def get_authenticated_session(self) -> requests.Session:
        """
        Get the authenticated session for making requests
        
        Returns:
            Authenticated requests.Session object
        """
        return self.session
    
    def save_session(self, filepath: str):
        """Save session cookies for later use"""
        cookies = self.session.cookies.get_dict()
        with open(filepath, 'w') as f:
            json.dump(cookies, f)
        print(f"✅ Session saved to {filepath}")
    
    def load_session(self, filepath: str) -> bool:
        """Load session cookies from file"""
        try:
            with open(filepath, 'r') as f:
                cookies = json.load(f)
            self.session.cookies.update(cookies)
            
            # Verify session is still valid
            response = self.session.get("https://substack.com/api/v1/user")
            if response.status_code == 200:
                print("✅ Session loaded and valid")
                return True
            else:
                print("⚠️ Session expired, need to re-authenticate")
                return False
                
        except Exception as e:
            print(f"❌ Could not load session: {e}")
            return False