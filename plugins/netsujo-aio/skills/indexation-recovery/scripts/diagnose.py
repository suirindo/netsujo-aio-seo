#!/usr/bin/env python3
"""indexation-recovery: 指定 URL の failure mode 分類（URL Inspection API）

⚠️ これは「原因を特定する」ツールではない。**渡した URL を調べるだけ**である。

原因の特定には必ず先に classify-coverage-export.py を使うこと:

    python3 classify-coverage-export.py <GSCドリルダウンexport.zip>

理由: GSC の Index Coverage には URL 一覧を返す API が存在せず、
Search Analytics API は impressions>0 の URL しか返さない。
ビルドアセット・ジャンク URL は impressions が付かないため
**API からは原理的に見えない**。このスクリプトだけで母集団を推定すると、
「API に見えている URL」に原因を誤帰属させる。
実例: netsujo.jp で未インデックス1,437件を「旧CMS URL が主犯」と診断したが、
ドリルダウン CSV では旧CMS URL は1,000件中0件、実際は99.9%がビルドアセットだった
（2026-07-21・9日間の誤診）。

このスクリプトの正しい用途:
  - classify-coverage-export.py で絞り込んだ real-page の状態確認
  - サイトマップ掲載ページの indexed 率サンプリング
  - 対応後の再クロール進捗の確認（lastCrawlTime）

Usage:
    python diagnose.py --site-url https://www.miyakodeit.com/ \\
        --credentials ~/.config/gcloud/gsc.json --urls <URL> [<URL> ...]

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
