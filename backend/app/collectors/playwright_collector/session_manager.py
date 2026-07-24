"""
Session Manager for Playwright Article Collector

Handles browser session/cookie persistence for authenticated article collection.
Cookies are stored per-site to maintain login state across collector runs.
"""

import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# Known custom Substack domains (sites using Substack with custom domains)
CUSTOM_SUBSTACK_DOMAINS = [
    'oneusefulthing.org',      # Ethan Mollick
    'llmwatch.com',            # LLM Watch
    'lumberjack-ai.com',       # LumberjackAI
    'platformer.news',         # Casey Newton
    'stratechery.com',         # Ben Thompson
    'thegeneralist.substack.com',
]

# Supported sites and their authentication indicators
SUPPORTED_SITES = {
    'substack': {
        'name': 'Substack',
        'domains': ['substack.com'] + CUSTOM_SUBSTACK_DOMAINS,
        'auth_indicator': 'substack.com/inbox',  # URL indicates logged in (redirects to login if not)
        'login_url': 'https://substack.com/sign-in',
        'test_url': 'https://substack.com/inbox',
    },
    'medium': {
        'name': 'Medium',
        'domains': ['medium.com'],
        'auth_indicator': 'data-testid="headerAvatar"',
        'login_url': 'https://medium.com/m/signin',
        'test_url': 'https://medium.com/me/settings',
    },
    'patreon': {
        'name': 'Patreon',
        'domains': ['patreon.com'],
        'auth_indicator': 'data-tag="logged-in-nav"',
        'login_url': 'https://www.patreon.com/login',
        'test_url': 'https://www.patreon.com/settings/account',
    },
}


class SessionManager:
    """Manages browser session/cookie persistence for authenticated sites."""

    def __init__(self, sessions_dir: Optional[str] = None):
        """
        Initialize the session manager.

        Args:
            sessions_dir: Directory to store session data. Defaults to
                         backend/data/playwright_sessions/
        """
        if sessions_dir:
            self.sessions_dir = Path(sessions_dir)
        else:
            # Default to backend/data/playwright_sessions/
            backend_dir = Path(__file__).parent.parent.parent.parent
            self.sessions_dir = backend_dir / 'data' / 'playwright_sessions'

        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions (owner only)
        try:
            os.chmod(self.sessions_dir, 0o700)
        except OSError:
            logger.warning("Could not set restrictive permissions on sessions directory")

        self.metadata_file = self.sessions_dir / 'sessions_metadata.json'
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load session metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load session metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}

    def _save_metadata(self) -> None:
        """Save session metadata to disk."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
            os.chmod(self.metadata_file, 0o600)
        except IOError as e:
            logger.error(f"Failed to save session metadata: {e}")

    def detect_site(self, url: str) -> Optional[str]:
        """
        Detect which supported site a URL belongs to.

        Args:
            url: The URL to check

        Returns:
            Site key (e.g., 'substack', 'medium') or None if not supported
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        for site_key, site_info in SUPPORTED_SITES.items():
            for site_domain in site_info['domains']:
                if domain.endswith(site_domain) or site_domain in domain:
                    return site_key

        # Check for custom Substack domains (e.g., oneusefulthing.substack.com)
        # Most Substack sites follow the pattern *.substack.com
        if 'substack' in domain:
            return 'substack'

        return None

    def get_site_dir(self, site: str) -> Path:
        """Get the directory for a site's session data."""
        site_dir = self.sessions_dir / site
        site_dir.mkdir(parents=True, exist_ok=True)
        return site_dir

    def get_cookies_path(self, site: str) -> Path:
        """Get the path to a site's cookies file."""
        return self.get_site_dir(site) / 'cookies.json'

    def get_state_path(self, site: str) -> Path:
        """Get the path to a site's browser state file."""
        return self.get_site_dir(site) / 'state.json'

    def has_session(self, site: str) -> bool:
        """Check if we have saved session data for a site."""
        cookies_path = self.get_cookies_path(site)
        return cookies_path.exists()

    def get_session_info(self, site: str) -> Optional[Dict]:
        """
        Get information about a site's saved session.

        Returns:
            Dict with session info or None if no session exists
        """
        if site not in self.metadata:
            if self.has_session(site):
                # Session exists but no metadata - create basic info
                return {
                    'site': site,
                    'has_cookies': True,
                    'created_at': None,
                    'last_used': None,
                    'is_valid': None  # Unknown until validated
                }
            return None

        return self.metadata[site]

    def save_cookies(self, site: str, cookies: List[Dict]) -> None:
        """
        Save cookies for a site.

        Args:
            site: Site identifier (e.g., 'substack')
            cookies: List of cookie dictionaries from Playwright
        """
        cookies_path = self.get_cookies_path(site)

        try:
            with open(cookies_path, 'w') as f:
                json.dump(cookies, f, indent=2)
            os.chmod(cookies_path, 0o600)

            # Update metadata
            now = datetime.now(timezone.utc).isoformat()
            if site not in self.metadata:
                self.metadata[site] = {
                    'created_at': now,
                    'last_used': now,
                    'cookie_count': len(cookies)
                }
            else:
                self.metadata[site]['last_used'] = now
                self.metadata[site]['cookie_count'] = len(cookies)

            self._save_metadata()
            logger.info(f"Saved {len(cookies)} cookies for {site}")

        except IOError as e:
            logger.error(f"Failed to save cookies for {site}: {e}")
            raise

    def load_cookies(self, site: str) -> Optional[List[Dict]]:
        """
        Load cookies for a site.

        Args:
            site: Site identifier

        Returns:
            List of cookie dictionaries or None if not found
        """
        cookies_path = self.get_cookies_path(site)

        if not cookies_path.exists():
            return None

        try:
            with open(cookies_path, 'r') as f:
                cookies = json.load(f)

            # Update last used time
            if site in self.metadata:
                self.metadata[site]['last_used'] = datetime.now(timezone.utc).isoformat()
                self._save_metadata()

            return cookies

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load cookies for {site}: {e}")
            return None

    def save_storage_state(self, site: str, state: Dict) -> None:
        """
        Save Playwright storage state (cookies + localStorage).

        Args:
            site: Site identifier
            state: Playwright storage state dictionary
        """
        state_path = self.get_state_path(site)

        try:
            with open(state_path, 'w') as f:
                json.dump(state, f, indent=2)
            os.chmod(state_path, 0o600)

            # Also save cookies separately for inspection
            if 'cookies' in state:
                self.save_cookies(site, state['cookies'])

            logger.info(f"Saved storage state for {site}")

        except IOError as e:
            logger.error(f"Failed to save storage state for {site}: {e}")
            raise

    def get_storage_state_path(self, site: str) -> Optional[str]:
        """
        Get path to storage state file if it exists.

        Returns:
            Path string or None if no state saved
        """
        state_path = self.get_state_path(site)
        return str(state_path) if state_path.exists() else None

    def delete_session(self, site: str) -> bool:
        """
        Delete all session data for a site.

        Args:
            site: Site identifier

        Returns:
            True if session was deleted, False if it didn't exist
        """
        site_dir = self.get_site_dir(site)

        if not site_dir.exists():
            return False

        import shutil
        try:
            shutil.rmtree(site_dir)
            if site in self.metadata:
                del self.metadata[site]
                self._save_metadata()
            logger.info(f"Deleted session for {site}")
            return True
        except OSError as e:
            logger.error(f"Failed to delete session for {site}: {e}")
            return False

    def list_sessions(self) -> Dict[str, Dict]:
        """
        List all saved sessions.

        Returns:
            Dict mapping site names to session info
        """
        sessions = {}

        for site_key in SUPPORTED_SITES:
            if self.has_session(site_key):
                sessions[site_key] = self.get_session_info(site_key)

        return sessions

    def get_site_config(self, site: str) -> Optional[Dict]:
        """Get configuration for a supported site."""
        return SUPPORTED_SITES.get(site)

    def validate_session(self, site: str, page_content: str) -> bool:
        """
        Validate if a session is still authenticated based on page content.

        Args:
            site: Site identifier
            page_content: HTML content of a test page

        Returns:
            True if session appears valid (user is logged in)
        """
        site_config = self.get_site_config(site)
        if not site_config:
            return False

        auth_indicator = site_config.get('auth_indicator', '')
        is_valid = auth_indicator in page_content

        # Update metadata
        if site in self.metadata:
            self.metadata[site]['is_valid'] = is_valid
            self.metadata[site]['last_validated'] = datetime.now(timezone.utc).isoformat()
            self._save_metadata()

        return is_valid
