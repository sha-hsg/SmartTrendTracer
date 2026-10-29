"""ACL Anthology import accepts every common link form (2026-10-29)."""
import pytest

from app.services.acl_anthology_service import normalize_acl_url

PAGE = 'https://aclanthology.org/2026.eacl-short.34/'


@pytest.mark.parametrize('value', [
    'https://aclanthology.org/2026.eacl-short.34.pdf',
    'https://aclanthology.org/2026.eacl-short.34/',
    'https://aclanthology.org/2026.eacl-short.34',
    'http://aclanthology.org/2026.eacl-short.34.pdf',
    'aclanthology.org/2026.eacl-short.34.pdf',
    'https://www.aclanthology.org/2026.eacl-short.34.pdf',
    'https://aclanthology.org/2026.eacl-short.34v2.pdf',
    'https://aclanthology.org/2026.eacl-short.34.bib',
    '  https://aclanthology.org/2026.eacl-short.34.pdf?download=1  ',
    '2026.eacl-short.34',
])
def test_forms_map_to_the_page(value):
    assert normalize_acl_url(value) == PAGE


def test_old_style_ids_and_multi_part_venues():
    assert normalize_acl_url('https://aclanthology.org/P19-1001.pdf') == 'https://aclanthology.org/P19-1001/'
    assert normalize_acl_url('https://aclanthology.org/2024.findings-emnlp.12/') == \
        'https://aclanthology.org/2024.findings-emnlp.12/'


@pytest.mark.parametrize('value', ['https://arxiv.org/abs/2401.00001', 'https://aclanthology.org/events/acl-2025/', ''])
def test_other_urls_are_rejected(value):
    with pytest.raises(ValueError):
        normalize_acl_url(value)
