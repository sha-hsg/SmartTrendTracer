"""Substack post header removed from article markdown (2026-10)."""
from app.utils.content_cleaner import strip_substack_byline as strip

RASCHKA = ("# Language Models for Text Classification\n\n### A Visual Guide\n\n"
           "[![Sebastian Raschka, PhD's avatar](https://substackcdn.com/image/fetch/w_36/x.jpeg)](<https://substack.com/@rasbt>)\n\n"
           "[Sebastian Raschka, PhD](<https://substack.com/@rasbt>)\n\nSep 29, 2026\n\n266\n\n16\n\n15\n\nShare\n\n"
           "The recently released Jev AI model has been quite a cultural phenomenon.")
TRILLIUM = ("# Introducing Trillium Labs\n\n### Fostering the open science of frontier AI.\n\n"
            "Oct 01, 2026\n\n60\n\n6\n\n6\n\nShare\n\nCross-posted by [Trillium Labs](<https://x.substack.com>)\n\nToday we unveil...")
FOOTER = "Body text.\n\n" + "More body. " * 400 + "\n\n1,104\n\n74\n\n102\n\nShare\n\nPreviousNext"


def test_strips_full_byline_keeps_title_and_body():
    out = strip(RASCHKA)
    assert out.startswith('# Language Models for Text Classification\n\n### A Visual Guide\n\nThe recently released')
    assert 'avatar' not in out and '266' not in out and 'Share' not in out


def test_strips_date_counters_without_author_block():
    out = strip(TRILLIUM)
    assert 'Oct 01, 2026' not in out and '\n60\n' not in out
    assert 'Cross-posted by' in out and out.startswith('# Introducing Trillium Labs')


def test_leaves_footer_and_plain_articles_alone():
    assert strip(FOOTER) == FOOTER
    plain = "# Title\n\nWe measured 266 samples.\n\n16 of them failed.\n\nShare your thoughts below."
    assert strip(plain) == plain
    assert strip('') == '' and strip(None) is None
