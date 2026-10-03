"""Weekly digest: facts are stored even when the LLM summary fails (2026-10)."""
import pytest

from app.services import digest_service as svc

WEEK = {'week_start': '2026-09-26T10:00:00+00:00', 'week_end': '2026-10-03T10:00:00+00:00',
        'stats': {'tweets': 3}, 'rising': [], 'declining': [], 'stable': [], 'anomalies': [],
        'new_papers': [{'id': 'p', 'title': 'A paper', 'source': 'arxiv', 'abstract': 'x'}],
        'new_articles': [], 'top_tweets': [], 'feed_suggestions': []}


class FakeLLM:
    def __init__(self, fail=False):
        self.fail, self.calls = fail, []

    def get_prompt(self, key):
        assert key == 'weekly_digest'
        return {'system': 'sys', 'user_template': 'From {week_start} to {week_end}: {data}'}

    def complete_text(self, task_type, user, system_prompt=None):
        self.calls.append((task_type, user))
        if self.fail:
            raise RuntimeError('provider down')
        return '## The week in three sentences\nok'


@pytest.fixture
def saved(monkeypatch):
    docs = []
    monkeypatch.setattr(svc, 'collect_week', lambda now=None: dict(WEEK))
    monkeypatch.setattr(svc.repo, 'save_digest', lambda doc: docs.append(doc) or 'id1')
    return docs


def test_summary_uses_trend_task_and_dates(saved):
    llm = FakeLLM()
    result = svc.generate_digest(llm=llm)
    assert result['summary_ok'] and result['week_start'] == '2026-09-26'
    task, prompt = llm.calls[0]
    assert task == 'trend_analysis' and prompt.startswith('From 2026-09-26 to 2026-10-03:')
    assert saved[0]['summary'].startswith('## The week')


def test_llm_failure_still_stores_facts(saved):
    result = svc.generate_digest(llm=FakeLLM(fail=True))
    assert result['summary_ok'] is False
    assert saved[0]['summary'] == '' and 'provider down' in saved[0]['summary_error']
    assert saved[0]['new_papers'][0]['title'] == 'A paper'


def test_prompt_template_exists_in_config():
    import json
    from pathlib import Path
    prompts = json.loads((Path(svc.__file__).resolve().parents[2] / 'prompts_config.json').read_text())
    assert {'system', 'user_template'} <= set(prompts['weekly_digest'])
    prompts['weekly_digest']['user_template'].format(week_start='a', week_end='b', data='c')
