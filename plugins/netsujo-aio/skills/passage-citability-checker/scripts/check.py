#!/usr/bin/env python3
"""passage content-readiness checker CLI

冒頭パッセージのローカル編集ヒューリスティックを計算する。
このスコアは引用確率や引用増加率を推定しない。

Scoring(0-100):
    Definition density   (25): "Xとは Y である" 形式の存在
    Statistic density    (20): 100文字あたりの数値出現率
    Answer-first         (19): 最初の文が直接回答か
    Entity clarity       (16): 固有名詞 + 括弧読み
    Citation hooks       (20): "N個の理由" "ステップ1〜N" 等

Usage:
    python check.py --url https://netsujo.jp/blog/bizdev-guide
    python check.py --file path/to/page.html
    python check.py --text "..."

Output: JSON with scores + rewrite suggestion
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path


def fetch_url(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; netsujo-aio/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def extract_lead(html: str, max_chars: int = 300) -> str:
    body = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    body = re.sub(r"<style[\s\S]*?</style>", " ", body, flags=re.IGNORECASE)
    m = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", body, re.IGNORECASE)
    after = body[m.end():] if m else body
    text = re.sub(r"<[^>]+>", " ", after)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def score_definition_density(passage: str) -> int:
    # 「Xとは Y です/である/のこと」型を探す
    pat = re.compile(r"[^。]+とは[^。]+(です|である|のこと|を指す|の総称)")
    return 25 if pat.search(passage) else 10


def score_statistic_density(passage: str) -> int:
    # 数字の出現数(年/%等含む)
    digits = len(re.findall(r"\d+", passage))
    pct = digits * 100 / max(1, len(passage)) * 100
    if digits >= 3 and pct >= 2:
        return 20
    if digits >= 1:
        return 12
    return 5


def score_answer_first(passage: str) -> int:
    # 最初の文の冒頭が定義型か(主語+とは)
    sentences = re.split(r"[。.\n]", passage)
    first = sentences[0] if sentences else ""
    if not first:
        return 5
    if "とは" in first or "です" in first[:40]:
        return 19
    if len(first) < 60:
        return 15
    return 8


def score_entity_clarity(passage: str) -> int:
    # 括弧付き読み・社名・会社/法人/協会の出現
    has_paren = bool(re.search(r"[（(][^)）]{2,12}[)）]", passage))
    has_org = bool(re.search(r"(株式会社|有限会社|NPO法人|協会|大学|国|京都府|京都市)", passage))
    score = 0
    if has_paren:
        score += 9
    if has_org:
        score += 7
    return min(score, 16)


def score_citation_hooks(passage: str) -> int:
    # "5つの" "Nステップ" "対策" "事例" 等
    hooks = re.findall(r"(\d+つの|\d+ステップ|\d+要素|\d+パターン|事例|対策|まとめ)", passage)
    if len(hooks) >= 3:
        return 20
    if len(hooks) >= 1:
        return 12
    return 5


def verdict(total: int) -> str:
    if total >= 80:
        return "Strong content readiness"
    if total >= 60:
        return "Acceptable, room for improvement"
    return "Rewrite candidate"


def main():
    p = argparse.ArgumentParser(description="Passage citability checker")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", help="URL を fetch して評価")
    g.add_argument("--file", help="HTML ファイルパス")
    g.add_argument("--text", help="生テキストを直接評価")
    args = p.parse_args()

    if args.url:
        html = fetch_url(args.url)
        passage = extract_lead(html)
        source = args.url
    elif args.file:
        html = Path(args.file).read_text(encoding="utf-8")
        passage = extract_lead(html)
        source = args.file
    else:
        passage = args.text[:300]
        source = "stdin"

    scores = {
        "definition_density": score_definition_density(passage),
        "statistic_density": score_statistic_density(passage),
        "answer_first": score_answer_first(passage),
        "entity_clarity": score_entity_clarity(passage),
        "citation_hooks": score_citation_hooks(passage),
    }
    total = sum(scores.values())

    out = {
        "source": source,
        "lead_passage": passage[:200] + ("…" if len(passage) > 200 else ""),
        "scores": scores,
        "total": total,
        "max": 100,
        "metricType": "contentReadiness",
        "verdict": verdict(total),
        "citationOutcome": "unmeasured",
    }
    if total < 80:
        out["recommendations"] = [
            "冒頭に「Xとは Y である」型の定義文を1文目に配置",
            "原典確認済みの数値がある場合のみ、冒頭で簡潔に示す",
            "固有名詞には括弧付きの読みを併記",
            "「N個の理由」「Nステップ」等の citation hook を入れる",
        ]
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
