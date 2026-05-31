#!/usr/bin/env python3
"""GA4 custom dimensions registrar.

Registers the 12 standard custom dimensions (or a YAML-provided catalog) on a
GA4 property via the Admin API. Dry-run by default. Idempotent: dimensions are
matched by (parameterName, scope) and skipped if already present.

Usage:
    python3 ga4-custom-dimensions.py --property 531238165 --dry-run
    python3 ga4-custom-dimensions.py --property 531238165 --apply
    python3 ga4-custom-dimensions.py --property 531238165 --list
    python3 ga4-custom-dimensions.py --property 531238165 --catalog custom.yaml --apply

Auth:
    GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
    GA4_PROPERTY_ID=531238165   # optional default
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from typing import Iterable

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

try:
    from google.oauth2 import service_account  # type: ignore
    from googleapiclient.discovery import build  # type: ignore
    from googleapiclient.errors import HttpError  # type: ignore
except ImportError:  # pragma: no cover
    service_account = None
    build = None
    HttpError = Exception


SCOPES = ["https://www.googleapis.com/auth/analytics.edit"]
API_NAME = "analyticsadmin"
API_VERSION = "v1beta"


SCOPE_MAP = {
    "event-scoped": "EVENT",
    "event": "EVENT",
    "user-scoped": "USER",
    "user": "USER",
    "item-scoped": "ITEM",
    "item": "ITEM",
}


@dataclass(frozen=True)
class Dimension:
    name: str            # display name shown in GA4 UI
    scope: str           # EVENT | USER | ITEM
    parameter: str       # parameterName as fired in dataLayer
    description: str

    @property
    def key(self) -> tuple[str, str]:
        return (self.parameter, self.scope)


STANDARD_CATALOG: list[Dimension] = [
    Dimension("CTAラベル", "EVENT", "cta_label",
              "CTA button label clicked by user"),
    Dimension("CTA位置", "EVENT", "cta_position",
              "Location of CTA on the page (hero/footer/sidebar)"),
    Dimension("記事カテゴリ", "EVENT", "article_category",
              "Blog article category slug"),
    Dimension("記事著者", "EVENT", "article_author",
              "Author name of the article"),
    Dimension("イベント参加形態", "EVENT", "event_attendance_mode",
              "Online / Offline / Mixed attendance mode"),
    Dimension("外部リンク先ドメイン", "EVENT", "outbound_domain",
              "Domain of clicked outbound link"),
    Dimension("サイト内検索クエリ", "EVENT", "search_query",
              "User-entered site search query"),
    Dimension("ユーザー階層", "USER", "user_tier",
              "User subscription tier (free/paid/enterprise)"),
    Dimension("サインアップ流入元", "USER", "signup_source",
              "Channel that drove the signup"),
    Dimension("読了率", "EVENT", "read_completion_pct",
              "Article read completion percent (25/50/75/100)"),
    Dimension("言語設定", "USER", "language_pref",
              "Preferred UI language (ja/en/...)"),
    Dimension("A/Bテスト variant", "EVENT", "experiment_variant",
              "Variant assigned in an A/B experiment"),
]


def load_catalog(path: str | None) -> list[Dimension]:
    if not path:
        return STANDARD_CATALOG
    if yaml is None:
        raise SystemExit("PyYAML is required for --catalog. pip install pyyaml")
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or []
    catalog: list[Dimension] = []
    for entry in raw:
        scope_raw = entry.get("scope", "event")
        scope = SCOPE_MAP.get(scope_raw.lower())
        if not scope:
            raise SystemExit(f"unknown scope: {scope_raw}")
        catalog.append(Dimension(
            name=entry["name"],
            scope=scope,
            parameter=entry["parameter"],
            description=entry.get("description", ""),
        ))
    return catalog


def build_client():
    if build is None or service_account is None:
        raise SystemExit(
            "google-api-python-client and google-auth are required.\n"
            "  pip install google-api-python-client google-auth")
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        raise SystemExit("GOOGLE_APPLICATION_CREDENTIALS not set")
    credentials = service_account.Credentials.from_service_account_file(
        creds_path, scopes=SCOPES)
    return build(API_NAME, API_VERSION, credentials=credentials,
                 cache_discovery=False)


def list_existing(client, property_id: str) -> list[dict]:
    parent = f"properties/{property_id}"
    items: list[dict] = []
    page_token = None
    while True:
        req = client.properties().customDimensions().list(
            parent=parent, pageToken=page_token, pageSize=200)
        resp = _retry(req.execute)
        items.extend(resp.get("customDimensions", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


def _retry(fn, attempts: int = 3, delay: float = 1.0):
    for attempt in range(attempts):
        try:
            return fn()
        except HttpError as e:
            status = getattr(e, "status_code", None) or getattr(
                e.resp, "status", 0) if hasattr(e, "resp") else 0
            if status in (429, 503) and attempt < attempts - 1:
                time.sleep(delay * (2 ** attempt))
                continue
            raise


def diff(catalog: list[Dimension], existing: list[dict]) -> tuple[
        list[Dimension], list[Dimension], list[tuple[Dimension, dict]]]:
    """Return (to_create, to_skip, conflicts)."""
    existing_by_key: dict[tuple[str, str], dict] = {
        (e["parameterName"], e["scope"]): e for e in existing
    }
    existing_by_param: dict[str, dict] = {
        e["parameterName"]: e for e in existing
    }
    to_create: list[Dimension] = []
    to_skip: list[Dimension] = []
    conflicts: list[tuple[Dimension, dict]] = []
    for dim in catalog:
        if dim.key in existing_by_key:
            to_skip.append(dim)
            continue
        if dim.parameter in existing_by_param:
            # same parameter name, different scope → conflict (scope is immutable)
            conflicts.append((dim, existing_by_param[dim.parameter]))
            continue
        to_create.append(dim)
    return to_create, to_skip, conflicts


def create_one(client, property_id: str, dim: Dimension) -> dict:
    parent = f"properties/{property_id}"
    body = {
        "parameterName": dim.parameter,
        "displayName": dim.name,
        "description": dim.description,
        "scope": dim.scope,
    }
    req = client.properties().customDimensions().create(
        parent=parent, body=body)
    return _retry(req.execute)


def print_table(rows: Iterable[Iterable[str]]) -> None:
    rows = list(rows)
    if not rows:
        return
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))


def cmd_list(client, property_id: str) -> int:
    existing = list_existing(client, property_id)
    if not existing:
        print(f"(no custom dimensions on property {property_id})")
        return 0
    rows = [("parameterName", "scope", "displayName")]
    for e in existing:
        rows.append((e["parameterName"], e["scope"], e.get("displayName", "")))
    print_table(rows)
    return 0


def cmd_dry_run(catalog, existing, property_id: str) -> int:
    to_create, to_skip, conflicts = diff(catalog, existing)
    for dim in to_create:
        print(f"[dry-run] would create: {dim.parameter} ({dim.scope})")
    for dim in to_skip:
        print(f"[skip]    already exists: {dim.parameter} ({dim.scope})")
    for dim, existing_dim in conflicts:
        print(f"[conflict] {dim.parameter} requested scope={dim.scope} "
              f"but already exists as scope={existing_dim['scope']}")
    print(f"[summary] {len(to_create)} to create, {len(to_skip)} already "
          f"exist, {len(conflicts)} conflicts")
    return 2 if conflicts else 0


def cmd_apply(client, catalog, existing, property_id: str) -> int:
    to_create, to_skip, conflicts = diff(catalog, existing)
    if conflicts:
        for dim, existing_dim in conflicts:
            print(f"[conflict] {dim.parameter} requested scope={dim.scope} "
                  f"but already exists as scope={existing_dim['scope']}",
                  file=sys.stderr)
        print("[abort] scope is immutable; resolve conflicts manually",
              file=sys.stderr)
        return 2
    for dim in to_skip:
        print(f"[skip]   {dim.parameter} ({dim.scope}) already exists")
    for dim in to_create:
        created = create_one(client, property_id, dim)
        print(f"[create] {dim.parameter} ({dim.scope}) → "
              f"{created.get('name')}")
    print(f"[done] created {len(to_create)}, skipped {len(to_skip)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--property", default=os.environ.get("GA4_PROPERTY_ID"),
                        help="GA4 property ID (numeric)")
    parser.add_argument("--catalog", help="YAML catalog path (optional)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", default=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--list", dest="list_mode", action="store_true")
    args = parser.parse_args(argv)

    if not args.property:
        parser.error("--property is required (or set GA4_PROPERTY_ID)")

    client = build_client()
    if args.list_mode:
        return cmd_list(client, args.property)

    catalog = load_catalog(args.catalog)
    existing = list_existing(client, args.property)
    if args.apply:
        return cmd_apply(client, catalog, existing, args.property)
    return cmd_dry_run(catalog, existing, args.property)


if __name__ == "__main__":
    sys.exit(main())
