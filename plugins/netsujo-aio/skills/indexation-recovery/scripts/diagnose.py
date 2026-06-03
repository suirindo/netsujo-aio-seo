#!/usr/bin/env python3
"""indexation-recovery 診断 CLI(scaffold)

GSC sitemap submitted URLs を走査し、未インデックス URL の failure mode を分類する。
完全な recovery flow は今後のリリースで実装予定。

Usage:
    python diagnose.py --site-url https://www.miyakodeit.com/ --credentials ~/.config/gcloud/gsc.json

Output: JSON with failure-mode classification per URL
"""

import argparse
import json
import sys

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:
    print("Install: pip install google-auth google-api-python-client", file=sys.stderr)
    sys.exit(2)


def classify(coverage: str, page_fetch: str, user_canonical: str, google_canonical: str) -> str:
    """Failure mode 分類"""
    if "Submitted and indexed" in coverage:
        return "indexed-ok"
    if "noindex" in coverage.lower():
        return "noindex-intentional"
    if "Discovered" in coverage and "not indexed" in coverage:
        return "discovered-not-indexed"  # 内部リンク強化が rec
    if "Crawled" in coverage and "not indexed" in coverage:
        return "crawled-not-indexed"  # 質を強化 + 内部リンク
    if user_canonical and google_canonical and user_canonical != google_canonical:
        return "canonical-mismatch"
    if "redirect" in coverage.lower():
        return "redirect-final-not-indexed"
    return "unknown"


def main():
    p = argparse.ArgumentParser(description="Indexation recovery diagnose")
    p.add_argument("--site-url", required=True)
    p.add_argument("--credentials", required=True, help="service account JSON path")
    p.add_argument("--urls", nargs="+", required=True, help="検査対象 URL list")
    args = p.parse_args()

    creds = service_account.Credentials.from_service_account_file(
        args.credentials,
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
    )
    svc = build("searchconsole", "v1", credentials=creds)

    results = []
    for url in args.urls:
        try:
            resp = svc.urlInspection().index().inspect(body={
                "inspectionUrl": url,
                "siteUrl": args.site_url,
            }).execute()
            idx = resp.get("inspectionResult", {}).get("indexStatusResult", {})
            mode = classify(
                idx.get("coverageState", ""),
                idx.get("pageFetchState", ""),
                idx.get("userCanonical", ""),
                idx.get("googleCanonical", ""),
            )
            results.append({
                "url": url,
                "failure_mode": mode,
                "coverage": idx.get("coverageState", ""),
                "user_canonical": idx.get("userCanonical", ""),
                "google_canonical": idx.get("googleCanonical", ""),
                "last_crawl": idx.get("lastCrawlTime", ""),
            })
        except Exception as e:
            results.append({"url": url, "error": str(e)})

    print(json.dumps({
        "site": args.site_url,
        "results": results,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
