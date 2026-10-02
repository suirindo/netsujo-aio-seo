#!/usr/bin/env python3
"""Review rendered Japanese lines, not source-code newlines. MIT License."""
import argparse
import json
import re
import sys
from pathlib import Path

# Editorial hints, NOT a complete Japanese grammar or JLREQ implementation.
PARTICLE = re.compile(r'^(?:を|は|が|に|の|も|へ|と|で)(?:[、。！？]|$)')
PUNCTUATION_HEAD = set('、。，．！？)]｝）］」』】〉》〗〙〛')
PUNCTUATION_END = set('([｛（［「『【〈《〖〘〚')


def utf16_len(text):
    return len(text.encode('utf-16-le')) // 2


def utf16_slice(text, start, end):
    return text.encode('utf-16-le')[start * 2:end * 2].decode('utf-16-le')


def review(data):
    findings = []

    def emit(level, code, target, line=None, detail=''):
        findings.append(dict(level=level, code=code, target=target, line=line, detail=detail))

    if not isinstance(data, dict) or data.get('schemaVersion') != 1 or not isinstance(data.get('elements'), list) or not data['elements']:
        emit('invalid', 'missing-evidence', '', detail='Require schemaVersion=1 and nonempty elements.')
        return findings
    for index, el in enumerate(data['elements']):
        if not isinstance(el, dict):
            emit('invalid', 'invalid-element', str(index)); continue
        target = str(el.get('target', index))
        text, lines = el.get('text'), el.get('lines')
        if not isinstance(text, str) or not text.strip() or not isinstance(lines, list) or not lines:
            emit('invalid', 'missing-lines', target); continue
        if not isinstance(el.get('overflow'), bool) or not isinstance(el.get('unsupported'), list) or not isinstance(el.get('protectedSpans'), list):
            emit('invalid', 'missing-required-fields', target); continue
        if el['unsupported']:
            emit('invalid', 'unsupported-layout', target, detail=str(el['unsupported']))
        total, previous_end, valid = utf16_len(text), 0, True
        for n, line in enumerate(lines, 1):
            try:
                start, end = line['start'], line['end']
                if type(start) is not int or type(end) is not int or not previous_end == start < end <= total or not isinstance(line['text'], str) or utf16_slice(text, start, end) != line['text']:
                    raise ValueError()
                previous_end = end
            except (KeyError, TypeError, ValueError, UnicodeError):
                valid = False
                emit('invalid', 'invalid-line-coverage', target, n)
        if previous_end != total:
            valid = False; emit('invalid', 'incomplete-line-coverage', target)
        if not valid:
            continue
        if el['overflow']:
            emit('fail', 'overflow', target, detail='Text exceeds the measured box or scroll area.')
        for span in el['protectedSpans']:
            try:
                a, b, phrase = span['start'], span['end'], span['text']
                if type(a) is not int or type(b) is not int or not 0 <= a < b <= total or not isinstance(phrase, str) or utf16_slice(text, a, b) != phrase:
                    raise ValueError()
                for n, line in enumerate(lines[:-1], 1):
                    if a < line['end'] < b:
                        emit('fail', 'protected-span-split', target, n, phrase)
            except (KeyError, TypeError, ValueError, UnicodeError):
                emit('invalid', 'invalid-protected-span', target)
        for n, line in enumerate(lines, 1):
            current = line['text'].strip()
            if not current:
                emit('review', 'blank-rendered-line', target, n); continue
            if current[0] in PUNCTUATION_HEAD:
                emit('review', 'punctuation-head', target, n, current[:12])
            if current[-1] in PUNCTUATION_END:
                emit('review', 'punctuation-end', target, n, current[-12:])
            if n > 1 and PARTICLE.match(current):
                emit('review', 'particle-head-candidate', target, n, lines[n-2]['text'][-12:] + '｜' + current[:12])
        if el.get('surface') in ('heading', 'label', 'caption', 'lead') and len(lines) > 1:
            tail = lines[-1]['text'].strip()
            if len(tail) <= 3:
                emit('review', 'tiny-display-tail', target, len(lines), tail)
    return findings


def exit_code(findings):
    if any(f['level'] == 'invalid' for f in findings):
        return 2
    return 1 if findings else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    args = parser.parse_args()
    try:
        findings = review(json.loads(args.evidence.read_text(encoding='utf-8')))
    except (OSError, ValueError, UnicodeError) as exc:
        findings = [dict(level='invalid', code='unreadable-evidence', detail=str(exc))]
    print(json.dumps({'automatedStatus': 'NO_AUTOMATED_FINDINGS' if not findings else 'NEEDS_REVIEW', 'findings': findings, 'requiresSemanticAndVisualReview': True}, ensure_ascii=False, indent=2))
    return exit_code(findings)


if __name__ == '__main__':
    sys.exit(main())
