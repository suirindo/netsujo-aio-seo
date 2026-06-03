#!/usr/bin/env python3
"""ai-citation-tracker snapshot CLI(scaffold)

ChatGPT/Perplexity/Gemini/AI Overview への brand citation を時系列で記録する。
完全実装は engine 別 API/Playwright 配線が必要(別リリース)。

このスケルトンは:
- snapshot 保存形式の例示
- Perplexity API を利用した最小限の citation 取得
- snapshot 差分 detection

Usage:
    PERPLEXITY_API_KEY=xxx python snapshot.py --query "京都 Web3 開発会社" --brand Netsujo --output ~/.config/ai-citations/2026-06-03.json
"""

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path


def query_perplexity(query: str, api_key: str) -> dict:
    """Perplexity Sonar API で query → citations を取得"""
    url = "https://api.perplexity.ai/chat/completions"
    body = json.dumps({
        "model": "sonar",
        "messages": [{"role": "user", "content": query}],
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_citations(resp: dict) -> list[str]:
    """Perplexity response から citations URL list を抽出"""
    return resp.get("citations", []) or []


def check_brand_mention(citations: list[str], brand_hosts: list[str]) -> bool:
    """citations のいずれかが brand_hosts 配列のいずれかをホストするか"""
    for c in citations:
        for host in brand_hosts:
            if host in c:
                return True
    return False


def main():
    p = argparse.ArgumentParser(description="AI citation snapshot")
    p.add_argument("--query", required=True)
    p.add_argument("--brand-hosts", nargs="+", default=["netsujo.jp", "miyakodeit.com"])
    p.add_argument("--output", help="snapshot 出力先 JSON")
    p.add_argument("--engine", default="perplexity", choices=["perplexity"])
    args = p.parse_args()

    if args.engine == "perplexity":
        api_key = os.environ.get("PERPLEXITY_API_KEY")
        if not api_key:
            print("PERPLEXITY_API_KEY env required", file=sys.stderr)
            sys.exit(2)
        resp = query_perplexity(args.query, api_key)
        citations = extract_citations(resp)
    else:
        sys.exit(2)

    mentioned = check_brand_mention(citations, args.brand_hosts)
    snapshot = {
        "snapshot_date": datetime.now().strftime("%Y-%m-%d"),
        "engine": args.engine,
        "query": args.query,
        "brand_hosts": args.brand_hosts,
        "citations": citations,
        "brand_mentioned": mentioned,
        "citation_count": len(citations),
    }
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Saved: {args.output}")
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
