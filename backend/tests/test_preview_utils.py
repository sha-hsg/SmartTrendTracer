"""Regression tests for the shared preview cleaner (DEF-006).

329/573 stored previews carried Substack banners, CDN URLs and markdown
autolinks because five call sites sliced raw markdown[:500]. These cases are
taken from the actual dirty data.
"""

import re

from app.utils.preview_utils import generate_preview

DIRTY = re.compile(r'<[a-z]+|substackcdn\.com|\]\(<|href=|!\[', re.I)


class TestGeneratePreview:
    def test_empty_label_autolink_removed(self):
        # The single biggest artifact source: [](<url>) with an EMPTY label —
        # the old regex required a non-empty label
        md = '[](<https://substack.com/@oneusefulthing>) Ethan Mollick Apr 13'
        out = generate_preview(md)
        assert out.startswith('Ethan Mollick')
        assert not DIRTY.search(out)

    def test_banner_image_link_removed(self):
        md = ('[![Interconnects AI](https://substackcdn.com/image/fetch/'
              '$s_!ZugE!,w_144,h_144/img.png)](<https://interconnects.ai>) '
              'Frontier post-training recipe review')
        out = generate_preview(md)
        assert 'Frontier post-training recipe review' in out
        assert not DIRTY.search(out)

    def test_nested_image_link_with_parens_in_url(self):
        # CDN fetch URLs contain parentheses; the naive regexes left
        # "1600x850.png)](<...>)" fragments behind
        md = ('[![alt](https://substackcdn.com/image/fetch/w_1456,c_limit,'
              'f_auto,q_auto:good,fl_progressive:steep/img_1600x850.png)]'
              '(<https://example.substack.com/p/post>) Microsoft finally '
              'released agent mode')
        out = generate_preview(md)
        assert 'Microsoft finally released agent mode' in out
        assert not DIRTY.search(out)

    def test_normal_link_keeps_label(self):
        out = generate_preview('See ["Jagged Frontier"](<https://oneusefulthing.org/p/x>) for details. ' + 'Prose. ' * 100)
        assert '"Jagged Frontier"' in out
        assert not DIRTY.search(out)

    def test_length_and_sentence_boundary(self):
        md = 'First sentence here. ' * 60
        out = generate_preview(md, length=200)
        assert len(out) <= 210
        assert out.endswith('.')

    def test_empty_input(self):
        assert generate_preview('') == ''
        assert generate_preview(None) == ''
