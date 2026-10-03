"""Paper Q&A: chunking, retrieval and citation wiring (2026-10)."""
import numpy as np
import pytest

from app.repositories.errors import InvalidInputError
from app.services import paper_qa_service as svc

MD = """# Great Paper<sup>*</sup>

Authors here and an abstract that is long enough to stand on its own as a section of text for retrieval purposes, really.

# <span id="page-1-0"></span>1 Introduction

""" + ("Intro paragraph about agent memory. " * 30) + """

### Fig. 1

tiny

## 2 Method [\\[Smith 2020\\]](#page-9-1)

""" + ("\n\n".join(["Method paragraph number %d explains the algorithm in detail. " % i * 6 for i in range(12)])) + """

# References

[1] Smith. Something. 2020.
[2] Doe. Else. 2021.

# A Appendix

Appendix text that should be kept because it comes after the reference list. Appendix text that should be kept because it comes after the reference list. Appendix text that should be kept because it comes after the reference list. Appendix text that should be kept because it comes after the reference list. 
"""


def test_chunking_cleans_headings_skips_references_and_splits():
    chunks = svc.chunk_markdown(MD)
    headings = [c['heading'] for c in chunks]
    # the short title block is merged into the following section, not lost
    assert headings[0] == '1 Introduction' and 'Authors here' in chunks[0]['text']
    assert '1 Introduction' in headings
    assert '2 Method [Smith 2020]' in headings
    assert not any('Smith. Something' in c['text'] for c in chunks)      # reference list dropped
    assert 'A Appendix' in headings                                        # resumes after references
    assert headings.count('2 Method [Smith 2020]') >= 2                   # long section split
    assert all(len(c['text']) <= svc.CHUNK_CHARS * 1.5 for c in chunks)
    assert not any(c['heading'] == 'Fig. 1' for c in chunks)              # tiny section merged forward


def test_retrieve_caps_chunks_per_paper():
    per_paper = {
        'long': [{'heading': f's{i}', 'text': 't', 'vector': [1.0, 0.0]} for i in range(10)],
        'short': [{'heading': 'x', 'text': 't', 'vector': [0.8, 0.6]}],
    }
    hits = svc.retrieve(np.array([1.0, 0.0]), per_paper, k=8, max_per_paper=4)
    assert [h['paper_id'] for h in hits].count('long') == 4
    assert 'short' in [h['paper_id'] for h in hits]


class FakeLLM:
    def __init__(self):
        self.user = None

    def get_prompt(self, key):
        assert key == 'paper_qa'
        return {'system': 's', 'user_template': 'Q: {question}\n{excerpts}'}

    def complete_text(self, task, user, system_prompt=None):
        assert task == 'rag_answer'
        self.user = user
        return 'Agent memory is discussed [1].'


def fake_embed(texts, is_query=False):
    vec = lambda t: np.array([1.0, 0.0]) if 'memory' in t.lower() else np.array([0.0, 1.0])
    return vec(texts[0]) if is_query else np.array([vec(t) for t in texts])


def test_ask_end_to_end(monkeypatch):
    cache = {}
    monkeypatch.setattr(svc.repo, 'paper_ids_for_concept', lambda c: ['p1'])
    monkeypatch.setattr(svc.repo, 'find_papers', lambda ids: [{'_id': 'p1', 'title': 'Great Paper', 'content': MD}])
    monkeypatch.setattr(svc.repo, 'get_chunks', lambda pid: cache.get(pid))
    monkeypatch.setattr(svc.repo, 'save_chunks', lambda pid, h, m, ch: cache.update({pid: {'content_hash': h, 'model': m, 'chunks': ch}}))
    monkeypatch.setattr(svc, '_embedding_model', lambda: 'test-model')
    llm = FakeLLM()
    out = svc.ask('What about memory?', concept='Agent Memory', llm=llm, embed=fake_embed)
    assert out['answer'].endswith('[1].')
    assert out['sources'][0]['section'] == '1 Introduction'
    assert '[1] Great Paper — 1 Introduction' in llm.user
    # second question uses the cache (no re-embedding of documents)
    calls = []
    svc.ask('memory again?', concept='Agent Memory', llm=FakeLLM(),
            embed=lambda t, is_query=False: calls.append(is_query) or fake_embed(t, is_query))
    assert calls == [True]


def test_ask_requires_scope_and_text(monkeypatch):
    with pytest.raises(InvalidInputError):
        svc.ask('q', paper_ids=[], concept=None, llm=FakeLLM(), embed=fake_embed)
    monkeypatch.setattr(svc.repo, 'find_papers', lambda ids: [{'_id': 'p', 'title': 't', 'content': ''}])
    with pytest.raises(InvalidInputError, match='full text'):
        svc.ask('q', paper_ids=['p'], llm=FakeLLM(), embed=fake_embed)
