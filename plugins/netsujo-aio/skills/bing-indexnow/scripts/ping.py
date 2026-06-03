#!/usr/bin/env python3
"""bing-indexnow ping CLI

Submit URLs to IndexNow protocol (Bing/Yandex/Seznam/Naver).
ChatGPT Search 87% Bing top10依存 / Copilot 100% Bing依存 のため
AI 検索流入の直接ドライバーとなる。

Usage:
    # Single URL
    python ping.py --host netsujo.jp --key-file public/abc.txt --url https://netsujo.jp/blog/new

    # Bulk(stdin から URL を行区切りで読む)
    cat urls.txt | python ping.py --host netsujo.jp --key-file public/abc.txt --bulk

    # Sitemap から自動取得して bulk submission
    python ping.py --host netsujo.jp --key-file public/abc.txt --from-sitemap https://netsujo.jp/sitemap.xml

Exit codes:
    0: success
    1: ping failed
    2: invalid arguments
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# XXE / billion-laughs 対策で defusedxml を必須化(fallback禁止・fail fast)
try:
    import defusedxml.ElementTree as ET  # type: ignore
except ImportError:
    print(
        "ERROR: defusedxml is required for safe XML parsing. "
        "Install with: pip install defusedxml",
        file=sys.stderr,
    )
    sys.exit(2)


ENDPOINT = "https://api.indexnow.org/IndexNow"


def read_key(key_file: Path) -> str:
    return key_file.read_text(encoding="utf-8").strip()


def ping_single(host: str, key: str, key_location: str, url: str) -> tuple[int, str]:
    params = urllib.parse.urlencode({"url": url, "key": key, "keyLocation": key_location})
    req = urllib.request.Request(f"{ENDPOINT}?{params}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read(500).decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read(500).decode("utf-8", errors="ignore")


def ping_bulk(host: str, key: str, key_location: str, urls: list[str]) -> tuple[int, str]:
    body = json.dumps({
        "host": host,
        "key": key,
        "keyLocation": key_location,
        "urlList": urls[:10000],
    }).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read(500).decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read(500).decode("utf-8", errors="ignore")


def urls_from_sitemap(sitemap_url: str) -> list[str]:
    req = urllib.request.Request(
        sitemap_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; netsujo-aio/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [el.text for el in root.findall(".//s:url/s:loc", ns) if el.text]


def main():
    p = argparse.ArgumentParser(description="IndexNow ping CLI")
    p.add_argument("--host", required=True, help="ホスト名(netsujo.jp など)")
    p.add_argument("--key-file", required=True, help="key.txt ファイルパス")
    p.add_argument("--url", help="単一URL")
    p.add_argument("--bulk", action="store_true", help="stdin から URL bulk")
    p.add_argument("--from-sitemap", help="sitemap.xml URL から自動取得")
    args = p.parse_args()

    key_file = Path(args.key_file)
    if not key_file.exists():
        print(f"Key file not found: {key_file}", file=sys.stderr)
        sys.exit(2)
    key = read_key(key_file)
    key_location = f"https://{args.host}/{key}.txt"

    if args.url:
        status, body = ping_single(args.host, key, key_location, args.url)
        print(f"HTTP {status}: {body}")
        sys.exit(0 if 200 <= status < 300 else 1)

    urls: list[str] = []
    if args.bulk:
        urls = [line.strip() for line in sys.stdin if line.strip()]
    elif args.from_sitemap:
        urls = urls_from_sitemap(args.from_sitemap)
    else:
        print("Specify --url, --bulk(stdin), or --from-sitemap", file=sys.stderr)
        sys.exit(2)

    if not urls:
        print("No URLs to submit", file=sys.stderr)
        sys.exit(2)

    print(f"Submitting {len(urls)} URLs to IndexNow…")
    status, body = ping_bulk(args.host, key, key_location, urls)
    print(f"HTTP {status}: {body}")
    sys.exit(0 if 200 <= status < 300 else 1)


if __name__ == "__main__":
    main()
