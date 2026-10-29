"""Classify LLM/embedding provider errors (no dependencies, usable everywhere).

A billing error (prepaid credits used up, quota exhausted) comes back as HTTP
429 like a rate limit, but waiting does not help: retrying it only delayed the
smoke check by a minute and timed out the RAG update (2026-10-29)."""

BILLING_MARKERS = (
    'credits are depleted',           # Google AI Studio prepay
    'credit balance is too low',      # Anthropic
    'insufficient_quota',             # OpenAI
)
# Not billing: Gemini's per-minute limit says "You exceeded your current quota, please
# check your plan and billing details" — transient, it must stay retryable.


def is_billing_error(error) -> bool:
    text = str(error).lower()
    return any(marker in text for marker in BILLING_MARKERS)


def is_rate_limit(error) -> bool:
    """Transient 429: worth a retry with backoff."""
    return '429' in str(error) and not is_billing_error(error)
