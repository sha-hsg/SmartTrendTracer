"""Summaries fit the model's context instead of a fixed 1000/50/50 cap (2026-10-18)."""
from app.repositories.analytics import fit_to_token_budget


def _tweets(n, length=200):
    return [{'_id': str(i), 'text': 'x' * length} for i in range(n)]


def test_everything_fits_a_large_context():
    tweets = _tweets(1723)
    assert fit_to_token_budget(tweets, [], [], token_budget=500_000) == tweets


def test_small_context_gets_an_even_sample_over_the_whole_period():
    tweets = _tweets(1000)
    kept = fit_to_token_budget(tweets, [], [], token_budget=10_000)
    assert 0 < len(kept) < 1000
    assert kept[0] is tweets[0] and int(kept[-1]['_id']) > 900      # spread, not the first N


def test_articles_and_papers_are_reserved_first():
    tweets = _tweets(100)
    docs = [{'title': 't'}] * 200
    assert len(fit_to_token_budget(tweets, docs, docs, token_budget=45_000)) < 100   # 200+200 docs take ~148k of 157k chars


def test_context_window_follows_override_and_registry():
    from app.services.llm_manager import get_llm_manager
    llm = get_llm_manager()
    ctx = llm.context_window('articleSummarization')
    assert ctx['max_input_tokens'] >= 128_000 and ctx['model']
    assert llm.context_window('no_such_task')['max_input_tokens'] == llm.DEFAULT_CONTEXT_TOKENS
