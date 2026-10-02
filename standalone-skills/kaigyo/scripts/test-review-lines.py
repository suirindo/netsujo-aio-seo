#!/usr/bin/env python3
"""Regression of evidence integrity and editorial hints. MIT License."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('review_lines', Path(__file__).with_name('review-lines.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def evidence(parts, surface='body', phrases=(), overflow=False):
    text = ''.join(parts)
    start, lines = 0, []
    for part in parts:
        end = start + mod.utf16_len(part)
        # Synthetic fixture geometry only; this is not rendering evidence.
        width = max(16, len(part) * 16)
        lines.append(dict(text=part, start=start, end=end, left=0, right=width, widthPx=width)); start = end
    spans = []
    for phrase in phrases:
        a = text.index(phrase)
        spans.append(dict(text=phrase, start=mod.utf16_len(text[:a]), end=mod.utf16_len(text[:a+len(phrase)])))
    return dict(schemaVersion=2, elements=[dict(text=text, lines=lines, measure=dict(fontSizePx=16, maxLineEm=36 if surface=='lead' else 40), protectedSpans=spans, overflow=overflow, unsupported=[], surface=surface)])


class ReviewTests(unittest.TestCase):
    def codes(self, data):
        return [x['code'] for x in mod.review(data)]

    def test_orphan_particle(self):
        self.assertIn('particle-head-candidate', self.codes(evidence(['どの関わり方で', 'も、目的を尊重します。'])))

    def test_independent_word_not_particle(self):
        self.assertNotIn('particle-head-candidate', self.codes(evidence(['もっと自由に、', 'もっと深く。'])))

    def test_selected_phrase_split(self):
        self.assertIn('protected-span-split', self.codes(evidence(['3つの事例', 'を、ご覧ください。'], phrases=['3つの事例を、'])))

    def test_selected_phrase_intact(self):
        self.assertEqual([], self.codes(evidence(['事業を紹介します。', '3つの事例を、ご覧ください。'], phrases=['3つの事例を、'])))

    def test_body_word_split_allowed(self):
        self.assertEqual([], self.codes(evidence(['この文章は日本語の本文を読', 'み進めるための長い説明です。'])))

    def test_tiny_display_tail(self):
        self.assertIn('tiny-display-tail', self.codes(evidence(['利用できま', 'す。'], surface='heading')))

    def test_body_tiny_tail_not_automatically_banned(self):
        self.assertNotIn('tiny-display-tail', self.codes(evidence(['利用できま', 'す。'])))

    def test_punctuation_head(self):
        self.assertIn('punctuation-head', self.codes(evidence(['紹介します', '。続きです。'])))

    def test_punctuation_end(self):
        self.assertIn('punctuation-end', self.codes(evidence(['サービス「', '紹介」です。'])))

    def test_overflow_fails(self):
        self.assertEqual(1, mod.exit_code(mod.review(evidence(['事業を紹介します。'], overflow=True))))

    def test_empty_evidence_invalid(self):
        self.assertEqual(2, mod.exit_code(mod.review(dict(schemaVersion=2, elements=[]))))

    def test_empty_text_invalid(self):
        self.assertEqual(2, mod.exit_code(mod.review(evidence([' ']))))

    def test_unsupported_invalid(self):
        data = evidence(['紹介します。']); data['elements'][0]['unsupported'] = ['ruby']
        self.assertEqual(2, mod.exit_code(mod.review(data)))

    def test_incomplete_text_not_passed(self):
        data = evidence(['紹介します。']); data['elements'][0]['lines'][0]['end'] -= 1
        self.assertEqual(2, mod.exit_code(mod.review(data)))

    def test_wrong_line_string_invalid(self):
        data = evidence(['紹介します。']); data['elements'][0]['lines'][0]['text'] = '別の文章'
        self.assertEqual(2, mod.exit_code(mod.review(data)))

    def test_missing_overflow_not_passed(self):
        data = evidence(['紹介します。']); del data['elements'][0]['overflow']
        self.assertEqual(2, mod.exit_code(mod.review(data)))

    def test_emoji_utf16_offsets(self):
        data = evidence(['🚀サービスは', '月額7万円です。'], phrases=['月額7万円'])
        self.assertEqual([], self.codes(data))

    def test_repeat_selected_span(self):
        data = evidence(['月額7', '万円で使えます。月額7万円です。'], phrases=['月額7万円'])
        self.assertIn('protected-span-split', self.codes(data))

    def test_invalid_span_not_passed(self):
        data = evidence(['月額7万円です。'], phrases=['月額7万円'])
        data['elements'][0]['protectedSpans'][0]['end'] = 999
        self.assertEqual(2, mod.exit_code(mod.review(data)))

    def test_schema_not_inferred(self):
        self.assertEqual(2, mod.exit_code(mod.review({'elements':[]})))

    def test_wide_line_without_bad_boundary_requires_review(self):
        self.assertIn('overlong-line', self.codes(evidence(['読みやすい文章を届けます。' * 4])))

    def test_short_text_in_wide_box_is_not_overlong(self):
        data = evidence(['会社概要'])
        data['elements'][0]['box'] = dict(width=1280)
        self.assertNotIn('overlong-line', self.codes(data))

    def test_longest_line_not_hidden_by_short_tail(self):
        self.assertIn('overlong-line', self.codes(evidence(['読みやすい文章を届けます。' * 4, '続きます。'])))

    def test_missing_measure_invalid(self):
        data = evidence(['紹介します。']); del data['elements'][0]['measure']
        self.assertEqual(2, mod.exit_code(mod.review(data)))

    def test_nan_geometry_invalid(self):
        data = evidence(['紹介します。']); data['elements'][0]['lines'][0]['widthPx'] = float('nan')
        self.assertEqual(2, mod.exit_code(mod.review(data)))

    def test_inconsistent_width_invalid(self):
        data = evidence(['紹介します。']); data['elements'][0]['lines'][0]['right'] += 100
        self.assertEqual(2, mod.exit_code(mod.review(data)))

    def test_body_cannot_drop_measure_budget(self):
        data = evidence(['紹介します。']); data['elements'][0]['measure']['maxLineEm'] = None
        self.assertEqual(2, mod.exit_code(mod.review(data)))

    def test_old_schema_cannot_pass(self):
        data = evidence(['紹介します。']); data['schemaVersion'] = 1
        self.assertEqual(2, mod.exit_code(mod.review(data)))


if __name__ == '__main__':
    unittest.main()
