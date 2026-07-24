"""
LLM Service helpers: Circuit breaker, error classification, and utility functions.
Extracted from llm_service.py to keep modules under 600 LOC.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def classify_error(error_msg: str) -> str:
    """Classify an LLM error message into a category for debugging (OBS-001)."""
    if 'connection' in error_msg.lower() or 'network' in error_msg.lower():
        return 'network'
    elif '429' in error_msg or 'rate limit' in error_msg.lower():
        return 'rate_limit'
    elif any(code in error_msg for code in ['500', '502', '503', '504']):
        return 'server_error'
    elif 'timeout' in error_msg.lower():
        return 'timeout'
    elif 'invalid' in error_msg.lower() or 'parse' in error_msg.lower():
        return 'parsing'
    elif 'auth' in error_msg.lower() or '401' in error_msg or '403' in error_msg:
        return 'auth'
    else:
        return 'unknown'


def is_transient_error(error_category: str) -> bool:
    """Check if an error category represents a transient (retryable) error."""
    return error_category in ['rate_limit', 'server_error', 'timeout', 'network']


def infer_provider_from_model(model: str) -> Optional[str]:
    """Infer provider from model name string."""
    model_lower = model.lower()
    if 'gemini' in model_lower:
        return 'google'
    elif 'claude' in model_lower:
        return 'anthropic'
    elif 'gpt' in model_lower or 'o1' in model_lower:
        return 'openai'
    return None


def build_model_config(model: str, temperature: float, max_tokens: int) -> Optional[Dict[str, Any]]:
    """Build a basic model config dict from a model name string."""
    provider = infer_provider_from_model(model)
    if provider is None:
        return None
    return {
        'provider': provider,
        'model': model,
        'temperature': temperature,
        'max_tokens': max_tokens
    }


class CircuitBreakerManager:
    """
    Circuit breaker pattern for LLM provider availability (OBS-004).

    Circuit states:
    - closed: Normal operation, requests proceed
    - open: Too many failures, requests fail fast
    - half-open: Testing if service recovered, allow one probe request
    """

    FAILURE_THRESHOLD = 5   # Open circuit after 5 consecutive failures
    RESET_TIMEOUT = 300     # Reset after 5 minutes (300 seconds)

    def __init__(self):
        # Format: {provider: {'failures': int, 'last_failure': datetime|None, 'state': str}}
        self._state: Dict[str, Dict] = {}

    def _get_state(self, provider: str) -> dict:
        """Get current circuit breaker state for a provider."""
        if provider not in self._state:
            self._state[provider] = {
                'failures': 0,
                'last_failure': None,
                'state': 'closed'
            }
        return self._state[provider]

    def check(self, provider: str) -> bool:
        """Check if circuit allows requests. Returns True if request should proceed."""
        circuit = self._get_state(provider)

        if circuit['state'] == 'closed':
            return True

        if circuit['state'] == 'open':
            if circuit['last_failure']:
                elapsed = (datetime.now(timezone.utc) - circuit['last_failure']).total_seconds()
                if elapsed >= self.RESET_TIMEOUT:
                    circuit['state'] = 'half-open'
                    logger.info(f"Circuit breaker for {provider}: HALF-OPEN (allowing probe request)")
                    return True
            logger.warning(f"Circuit breaker for {provider}: OPEN (failing fast)")
            return False

        # half-open: allow the probe request
        return True

    def record_success(self, provider: str):
        """Record successful request, potentially closing the circuit."""
        circuit = self._get_state(provider)
        if circuit['state'] != 'closed':
            logger.info(f"Circuit breaker for {provider}: CLOSED (recovered)")
        circuit['failures'] = 0
        circuit['state'] = 'closed'

    def record_failure(self, provider: str):
        """Record failed request, potentially opening the circuit."""
        circuit = self._get_state(provider)
        circuit['failures'] += 1
        circuit['last_failure'] = datetime.now(timezone.utc)

        if circuit['state'] == 'half-open':
            circuit['state'] = 'open'
            logger.warning(f"Circuit breaker for {provider}: OPEN (probe failed, {circuit['failures']} total failures)")
        elif circuit['failures'] >= self.FAILURE_THRESHOLD:
            circuit['state'] = 'open'
            logger.warning(f"Circuit breaker for {provider}: OPEN (threshold reached: {circuit['failures']} failures)")

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for all providers (for monitoring)."""
        status = {
            'config': {
                'failure_threshold': self.FAILURE_THRESHOLD,
                'reset_timeout_seconds': self.RESET_TIMEOUT
            },
            'providers': {}
        }

        for provider, circuit in self._state.items():
            time_since_failure = None
            time_until_reset = None

            if circuit['last_failure']:
                elapsed = (datetime.now(timezone.utc) - circuit['last_failure']).total_seconds()
                time_since_failure = round(elapsed, 1)
                if circuit['state'] == 'open':
                    time_until_reset = max(0, round(self.RESET_TIMEOUT - elapsed, 1))

            status['providers'][provider] = {
                'state': circuit['state'],
                'failures': circuit['failures'],
                'last_failure': circuit['last_failure'].isoformat() if circuit['last_failure'] else None,
                'time_since_failure_seconds': time_since_failure,
                'time_until_reset_seconds': time_until_reset
            }

        # Add providers that haven't been used yet
        known_providers = ['openai', 'anthropic', 'google', 'xai']
        for provider in known_providers:
            if provider not in status['providers']:
                status['providers'][provider] = {
                    'state': 'closed',
                    'failures': 0,
                    'last_failure': None,
                    'time_since_failure_seconds': None,
                    'time_until_reset_seconds': None
                }

        return status

    def reset(self, provider: str) -> bool:
        """Manually reset circuit breaker for a provider."""
        if provider in self._state:
            self._state[provider] = {
                'failures': 0,
                'last_failure': None,
                'state': 'closed'
            }
            logger.info(f"Circuit breaker for {provider}: MANUALLY RESET to closed")
            return True
        return False
