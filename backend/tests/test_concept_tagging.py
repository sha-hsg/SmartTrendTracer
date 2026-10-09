"""Shared concept tagging (P2 2026-10: one path for job, batch and suggestions)."""
from app.services import concept_tagging as ct


def test_parse_concepts_tolerates_fences_and_strings():
    raw = 'Sure:\n```json\n[{"display_name": "Hugging Face", "entity_type": "organisation"}, "Kimi K3", {"x": 1}]\n```'
    out = ct.parse_concepts(raw)
    assert [c['display_name'] for c in out] == ['Hugging Face', 'Kimi K3']
    assert out[0]['slug'] == 'hugging_face' and out[1]['entity_type'] == 'topic'
    assert ct.parse_concepts('no json here') == []


class FakeService:
    def __init__(self, existing=()):
        self.existing, self.added = list(existing), []

    def get_tags_for_content(self, *_):
        return [{'slug': s} for s in self.existing]

    def add_tag(self, ctype, cid, name, preserve_display_name=True):
        self.added.append(name)
        return True, 'id'


def test_tag_item_applies_new_and_skips_existing(monkeypatch):
    monkeypatch.setattr(ct.repo, 'load_item', lambda t, i: {'title': '', 'author': '', 'text': 'x'})
    marked = []
    monkeypatch.setattr(ct.repo, 'mark_no_concepts', lambda t, i: marked.append(i))
    monkeypatch.setattr(ct, 'suggest', lambda *a, **k: (ct.parse_concepts('["LLM", "Kimi K3"]'), 'm'))
    svc = FakeService(existing=['llm'])
    result = ct.tag_item('tweet', '1', concept_service=svc)
    assert result == {'new': ['Kimi K3'], 'skipped': 1, 'failed': 0} and svc.added == ['Kimi K3'] and marked == []


def test_llm_failure_does_not_mark_item(monkeypatch):
    monkeypatch.setattr(ct.repo, 'load_item', lambda t, i: {'text': 'x'})
    marked = []
    monkeypatch.setattr(ct.repo, 'mark_no_concepts', lambda t, i: marked.append(i))

    def boom(*a, **k):
        raise ct.SuggestionError('down')
    monkeypatch.setattr(ct, 'suggest', boom)
    assert 'error' in ct.tag_item('paper', 'p', concept_service=FakeService()) and marked == []


def test_nothing_found_marks_item_as_tagged(monkeypatch):
    monkeypatch.setattr(ct.repo, 'load_item', lambda t, i: {'text': 'x'})
    marked = []
    monkeypatch.setattr(ct.repo, 'mark_no_concepts', lambda t, i: marked.append(i))
    monkeypatch.setattr(ct, 'suggest', lambda *a, **k: ([], 'm'))
    ct.tag_item('article', 'a', concept_service=FakeService())
    assert marked == ['a']
