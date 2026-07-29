#!/usr/bin/env python3
"""ai-citation-tracker snapshot CLI (Perplexity adapter)

ChatGPT/Perplexity/Gemini/AI Overview への brand citation を時系列で記録する。
完全実装は engine 別 API/Playwright 配線が必要(別リリース)。

このアダプターは:
- ai-citation-snapshot/v1 の保存
- Perplexity API を利用した最小限の citation 取得
- 応答本文・質問文・cookie・API key を snapshot から除外

Usage:
    PERPLEXITY_API_KEY=xxx python snapshot.py \
      --query "京都 Web3 開発会社" \
      --site-id netsujo \
      --target-id N-A-11 \
      --variant-id N-A-11-v1 \
      --brand-hosts netsujo.jp \
      --output reports/ai-citations/run.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


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


def citation_host(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    return parsed.hostname


def build_snapshot(
    *,
    site_id: str,
    target_id: str,
    variant_id: str,
    engine: str,
    model: str,
    locale: str,
    brand_hosts: list[str],
    citations: list[str],
    observed_at: str,
) -> dict:
    """Build a strict snapshot without retaining the submitted question."""
    citation_hosts = sorted({
        host for url in citations if (host := citation_host(url)) is not None
    })
    own_citations = [
        url
        for url in citations
        if any(
            host == brand or host.endswith(f".{brand}")
            for brand in brand_hosts
            if (host := citation_host(url)) is not None
        )
    ]
    mentioned = bool(own_citations)
    condition_id = f"{engine}:{locale}:{variant_id}:{model}"
    digest = hashlib.sha256(
        f"{site_id}:{condition_id}:{observed_at}".encode("utf-8")
    ).hexdigest()[:12]
    snapshot_id = f"ai-{digest}"
    return {
        "contract": "ai-citation-snapshot/v1",
        "schemaVersion": 1,
        "snapshotId": snapshot_id,
        "siteId": site_id,
        "observedAt": observed_at,
        "status": "success",
        "observations": [
            {
                "targetId": target_id,
                "observedAt": observed_at,
                "engine": engine,
                "model": model,
                "locale": locale,
                "variantId": variant_id,
                "runCount": 1,
                "successCount": 1,
                "ownMentionCount": 1 if mentioned else 0,
                "ownCitationCount": 1 if mentioned else 0,
                "ownCitationUrls": own_citations,
                "competitorDomains": [
                    host
                    for host in citation_hosts
                    if not any(
                        host == brand or host.endswith(f".{brand}")
                        for brand in brand_hosts
                    )
                ],
                "stability": "volatile" if mentioned else "not_cited",
                "factCheck": "unmeasured",
                "snapshotRef": snapshot_id,
            }
        ],
        "providerFailures": [],
    }


def main():
    p = argparse.ArgumentParser(description="AI citation snapshot")
    p.add_argument("--query", required=True)
    p.add_argument("--site-id", required=True)
    p.add_argument("--target-id", required=True)
    p.add_argument("--variant-id", required=True)
    p.add_argument("--locale", default="ja-JP")
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

    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    snapshot = build_snapshot(
        site_id=args.site_id,
        target_id=args.target_id,
        variant_id=args.variant_id,
        engine=args.engine,
        model="sonar",
        locale=args.locale,
        brand_hosts=args.brand_hosts,
        citations=citations,
        observed_at=observed_at,
    )
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
