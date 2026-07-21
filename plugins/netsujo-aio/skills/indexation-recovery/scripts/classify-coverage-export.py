#!/usr/bin/env python3
"""GSC「ページのインデックス登録」ドリルダウンCSVを分類する。

このスクリプトが存在する理由:
GSC の Index Coverage レポートには **URL 一覧を返す API が無い**。
Search Analytics API は impressions>0 の URL しか返さないため、
ビルドアセットやジャンク URL は API からは原理的に見えない。
結果として API だけで原因を推定すると、必ず「見えている URL」に
原因を誤帰属させる。実際に netsujo.jp で9日間の誤診が起きた（2026-07-21）。

正しい手順は「GSC UI → 理由行をクリック → エクスポート」で得た
CSV をこのスクリプトに通すこと。

Usage:
    python3 classify-coverage-export.py <export.zip|表.csv> [--json]

入力:
    GSC UI の「ページのインデックス登録」→ 理由行をクリック →
    右上「エクスポート」→ zip をダウンロード（中の「表.csv」を使う）
    zip をそのまま渡してよい（日本語ファイル名のまま解凍できる）。
"""

import argparse
import csv
import datetime as dt
import io
import json
import re
import sys
import urllib.parse
import zipfile
from collections import Counter

# 分類は「対応方法が変わる単位」で切る。件数の内訳より
# 「何をすべきか」が一意に決まることを優先している。
CATEGORIES = [
    # (ラベル, 判定関数, 推奨対応)
    (
        "build-asset",
        lambda p: p.startswith("/_next/") or p.startswith("/static/") or "/__nuxt/" in p,
        "X-Robots-Tag: noindex をアセットパスへ付与する。"
        "robots.txt の Disallow は使わない（レンダリング用フェッチまで止まり逆効果）",
    ),
    (
        "favicon-icon",
        lambda p: re.match(r"^/(favicon|icon|apple-icon|apple-touch-icon)[.\-]", p) is not None,
        "同上。favicon 系はアセットルールの対象外になりがちなので個別に指定する",
    ),
    (
        "og-image-route",
        lambda p: "opengraph-image" in p or "twitter-image" in p,
        "同上。動的OG画像ルートも検索インデックス不要",
    ),
    (
        "other-static-file",
        lambda p: re.search(
            r"\.(woff2?|ttf|otf|eot|css|js|mjs|map|png|jpe?g|svg|ico|webp|avif|gif|mp4|webm|wasm|webmanifest)(\?|$)",
            p,
        ) is not None,
        "配信元を確認のうえ noindex。サイト本体のページではない\n                       ※ .pdf は検索対象になりうる実コンテンツなので、ここでは除外し real-page 扱いにしている",
    ),
    (
        "query-variant",
        lambda p: "?" in p,
        "自己 canonical で正規化されていれば対応不要。要 canonical 確認",
    ),
    (
        "real-page",
        lambda p: True,
        "★ここだけが本当の課題。内部リンク強化・内容の独自性・sitemap再送信。\n                       impressions順に優先度を付ける（Indexing APIは公式にはJobPosting/BroadcastEvent限定）",
    ),
]

# デプロイごとに URL を増やすキャッシュバスターの既知パターン。
# これが多いと「デプロイ回数に比例して未インデックスが増える」状態になる。
DEPLOY_PARAM_PATTERNS = {
    "dpl": r"[?&]dpl=([^&]+)",           # Vercel Skew Protection
    "buildId": r"[?&]buildId=([^&]+)",
    "v": r"[?&]v=([0-9a-f]{8,})",
    "rev": r"[?&]rev=([^&]+)",
}


def load_rows(path: str) -> list[dict]:
    """zip でも csv でも受け取る。GSC の zip は日本語ファイル名を含む。"""
    if path.lower().endswith(".zip"):
        z = zipfile.ZipFile(path)
        # 「表.csv」= URL 一覧。「メタデータ.csv」「チャート.csv」は別物。
        names = [n for n in z.namelist() if n.endswith(".csv")]
        target = None
        for n in names:
            head = z.read(n)[:200].decode("utf-8", "replace")
            if head.lstrip("﻿").startswith("URL"):
                target = n
                break
        if target is None:
            print(
                "エラー: URL 一覧の CSV が zip 内に見つかりません。\n"
                "  取得した zip がサマリー（理由別集計）の可能性があります。\n"
                "  GSC UI で『クロール済み - インデックス未登録』などの"
                "**理由行をクリックして開いた先**からエクスポートしてください。\n"
                f"  zip の中身: {names}",
                file=sys.stderr,
            )
            sys.exit(2)
        data = z.read(target)
    else:
        data = open(path, "rb").read()
    text = data.decode("utf-8-sig", "replace")
    return list(csv.DictReader(io.StringIO(text)))


def path_of(url: str) -> str:
    """URL からパス+クエリを取り出す。相対URL・大文字スキームも扱う。"""
    parts = urllib.parse.urlsplit(url.strip())
    p = parts.path or "/"
    if parts.query:
        p += "?" + parts.query
    return p


def classify(p: str) -> tuple[str, str]:
    for label, pred, action in CATEGORIES:
        if pred(p):
            return label, action
    return "real-page", ""


def main() -> int:
    ap = argparse.ArgumentParser(description="GSC coverage drilldown classifier")
    ap.add_argument("path", help="GSC エクスポート zip または 表.csv")
    ap.add_argument("--json", action="store_true", help="JSON で出力")
    ap.add_argument("--list-real", action="store_true", help="real-page を全件表示")
    args = ap.parse_args()

    rows = load_rows(args.path)
    if not rows:
        print("エラー: 行がありません", file=sys.stderr)
        return 2

    url_key = next((k for k in rows[0] if k and k.strip().upper() == "URL"), None)
    if url_key is None:
        print(f"エラー: URL 列がありません（列: {list(rows[0])}）", file=sys.stderr)
        return 2
    # 「前回のクロール」列はロケールで名前が変わる。列名ではなく
    # 「値が日付として読めるか」で同定する（列順に依存すると別の列を拾う）。
    def looks_like_date(v: str) -> bool:
        v = (v or "").strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}", v):
            return False
        try:
            dt.date.fromisoformat(v[:10])
            return True
        except ValueError:
            return False

    crawl_key = None
    for k in rows[0]:
        if not k or k == url_key:
            continue
        sample = [r.get(k, "") for r in rows[:20]]
        if sum(looks_like_date(v) for v in sample) >= max(1, len(sample) // 2):
            crawl_key = k
            break

    counts = Counter()
    actions: dict[str, str] = {}
    real_pages: list[tuple[str, str]] = []
    deploy_ids: dict[str, set] = {k: set() for k in DEPLOY_PARAM_PATTERNS}
    crawl_dates: list[str] = []

    for r in rows:
        url = (r.get(url_key) or "").strip()
        if not url:
            continue
        p = path_of(url)
        label, action = classify(p)
        counts[label] += 1
        actions[label] = action
        if label == "real-page":
            real_pages.append((r.get(crawl_key, "") if crawl_key else "", p))
        for name, pat in DEPLOY_PARAM_PATTERNS.items():
            m = re.search(pat, url)
            if m:
                deploy_ids[name].add(m.group(1))
        if crawl_key and looks_like_date(r.get(crawl_key, "")):
            crawl_dates.append(r[crawl_key].strip()[:10])

    total = sum(counts.values())
    if total == 0:
        print("エラー: URL 行が0件です（URL列が空の可能性）", file=sys.stderr)
        return 2
    asset_like = sum(
        counts[k] for k in ("build-asset", "favicon-icon", "og-image-route", "other-static-file")
    )
    result = {
        "total_rows": total,
        "categories": {
            k: {"count": v, "pct": round(v / total * 100, 1), "action": actions[k]}
            for k, v in counts.most_common()
        },
        "asset_share_pct": round(asset_like / total * 100, 1),
        "real_pages": [{"last_crawl": d, "path": p} for d, p in sorted(real_pages)],
        "deploy_cache_busters": {
            k: len(v) for k, v in deploy_ids.items() if v
        },
        "crawl_date_range": (
            {"min": min(crawl_dates), "max": max(crawl_dates)} if crawl_dates else None
        ),
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"=== GSC カバレッジ内訳（{total} 行）===\n")
    for k, v in counts.most_common():
        print(f"  {k:20s} {v:6d}  ({v/total*100:5.1f}%)")
        print(f"  {'':20s}         → {actions[k]}")
    print()

    busters = {k: len(v) for k, v in deploy_ids.items() if v}
    if busters:
        print("⚠ デプロイごとに URL を増やすキャッシュバスターを検出:")
        for k, n in busters.items():
            print(f"    ?{k}= … ユニーク値 {n} 個")
        print(
            "  → 同一ファイルがデプロイのたびに別 URL として発行されている可能性が高い。\n"
            "    この状態ではデプロイ回数に比例して未インデックスが増え、\n"
            "    生成を止めない限り自然減衰は期待しにくい。\n"
            "    アセットへ X-Robots-Tag: noindex を付与し、可能ならパラメータ自体を止める。\n"
            "    ※ 生成が止まったかは本番HTMLに当該パラメータが残っていないかで確認する。\n"
        )

    if asset_like / total > 0.5:
        print(
            f"★ 判定: 観測サンプルの {asset_like}件（{asset_like/total*100:.1f}%）が"
            "ビルド成果物・静的ファイル。\n"
            "  『コンテンツがインデックスされない問題』ではなく"
            "『アセットのインデックス肥大』の疑いが強い。\n"
            "  ただし検索流入への実害の有無は本スクリプトだけでは判定できない。\n"
            "  GSC の impressions とサイトマップ掲載ページの indexed 率を突合して確認すること。\n"
            "  いずれにせよ未インデックス件数そのものを KPI にはしない。\n"
        )

    print(f"★ 対応が必要な実コンテンツページ: {counts['real-page']} 件")
    show = result["real_pages"] if args.list_real else result["real_pages"][:20]
    for e in show:
        print(f"    {e['last_crawl']}  {e['path']}")
    if not args.list_real and counts["real-page"] > 20:
        print(f"    …他 {counts['real-page']-20} 件（--list-real で全件）")

    if result["crawl_date_range"]:
        print(
            f"\nクロール日レンジ: {result['crawl_date_range']['min']} 〜 "
            f"{result['crawl_date_range']['max']}"
        )
        print("  最新日が数日以上前で止まっていれば、その時点で流入が止まった可能性がある")

    print(
        "\n注意: GSC のドリルダウンエクスポートは最大1,000件。"
        "\n  レポート上の総件数がこれを超える場合、残りは未観測であることを報告に明記すること。"
        "\n  また GSC の抽出順は非公開のため、この1,000件は母集団の無作為標本とは限らない。"
        "\n  報告では『観測サンプル』と明示し、全体比の断定を避けること。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
