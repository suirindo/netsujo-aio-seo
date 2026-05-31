#!/usr/bin/env python3
"""
jsonld-breadcrumb.py — Schema.org BreadcrumbList JSON-LD generator.

Generates BreadcrumbList JSON-LD from a URL pathname plus a label dictionary,
or emits a Next.js App Router React component that resolves breadcrumbs at
runtime via usePathname().

Usage:
  python3 jsonld-breadcrumb.py --path /blog/foo --config breadcrumb-config.yaml --output schema.json
  python3 jsonld-breadcrumb.py --config breadcrumb-config.yaml --format react --output BreadcrumbSchema.tsx
  python3 jsonld-breadcrumb.py --scan ./app/ --config breadcrumb-config.yaml --output BreadcrumbSchema.tsx

YAML config format:
  site: https://netsujo.jp
  inLanguage: ja
  labels:
    /: ホーム
    /blog: ブログ
    /blog/[slug]: "{title}"
    /events: イベント
    /company: 会社概要

React component emitted (sketch):

    "use client";
    import { usePathname } from "next/navigation";
    import Script from "next/script";

    const SITE = "https://netsujo.jp";
    const LABELS: Record<string, string> = { /* loaded from yaml */ };

    export function BreadcrumbSchema({ title }: { title?: string }) {
      const pathname = usePathname();
      // walk segments, resolve labels, emit BreadcrumbList JSON-LD
      // - position starts at 1, increments by 1
      // - last ListItem omits `item`
      // - dynamic [slug] resolved via `title` prop
    }
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore


# ---------- config ----------

def load_config(config_path: str) -> dict[str, Any]:
    """Load YAML config with site, inLanguage, labels map."""
    if yaml is None:
        raise SystemExit("PyYAML required: pip install pyyaml")
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg.setdefault("site", "")
    cfg.setdefault("inLanguage", "ja")
    cfg.setdefault("labels", {})
    return cfg


# ---------- path -> breadcrumb ----------

DYNAMIC_SEG = re.compile(r"^\[(\.\.\.)?(\w+)\]$")
GROUP_SEG = re.compile(r"^\((\w+)\)$")        # App Router route group, skipped in URL
PARALLEL_SEG = re.compile(r"^@(\w+)$")        # App Router parallel slot, skipped


def normalize_path(path: str) -> str:
    """Ensure leading slash, no trailing slash (except root)."""
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return path


def segments_of(path: str) -> list[str]:
    """Split a URL path into URL-visible segments (group/parallel stripped)."""
    if path == "/":
        return []
    parts = [p for p in path.split("/") if p]
    visible: list[str] = []
    for p in parts:
        if GROUP_SEG.match(p) or PARALLEL_SEG.match(p):
            continue
        visible.append(p)
    return visible


def resolve_label(segment_path: str, labels: dict[str, str], title: str | None) -> str:
    """
    Resolve a segment path (e.g. /blog or /blog/[slug]) to a human label.
    `{title}` placeholder is replaced with the runtime title.
    """
    if segment_path in labels:
        raw = labels[segment_path]
        if "{title}" in raw:
            if not title:
                raise ValueError(
                    f"Dynamic segment {segment_path} requires a title but none was provided"
                )
            return raw.replace("{title}", title)
        return raw
    # try dynamic-segment match: /blog/foo against /blog/[slug]
    parts = segment_path.split("/")
    for pattern, raw in labels.items():
        ppart = pattern.split("/")
        if len(ppart) != len(parts):
            continue
        if all(a == b or DYNAMIC_SEG.match(b) for a, b in zip(parts, ppart)):
            if "{title}" in raw and not title:
                raise ValueError(
                    f"Dynamic segment {pattern} requires a title but none was provided"
                )
            return raw.replace("{title}", title or "")
    # fallback: prettify last segment
    last = parts[-1] if parts and parts[-1] else "ホーム"
    return last.replace("-", " ").replace("_", " ")


def build_breadcrumb(
    path: str,
    site: str,
    labels: dict[str, str],
    in_language: str = "ja",
    title: str | None = None,
    omit_last_url: bool = True,
) -> dict[str, Any]:
    """Build a BreadcrumbList JSON-LD dict from a path + labels."""
    path = normalize_path(path)
    segs = segments_of(path)

    items: list[dict[str, Any]] = []
    # position 1: home
    home_label = labels.get("/", "Home")
    items.append({
        "@type": "ListItem",
        "position": 1,
        "name": home_label,
        "item": f"{site.rstrip('/')}/",
    })

    accumulated = ""
    for i, seg in enumerate(segs):
        accumulated = f"{accumulated}/{seg}"
        is_last = (i == len(segs) - 1)
        label = resolve_label(accumulated, labels, title if is_last else None)
        item: dict[str, Any] = {
            "@type": "ListItem",
            "position": i + 2,
            "name": label,
        }
        if not (is_last and omit_last_url):
            item["item"] = f"{site.rstrip('/')}{accumulated}"
        items.append(item)

    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "inLanguage": in_language,
        "itemListElement": items,
    }


# ---------- validation ----------

def validate(schema: dict[str, Any]) -> list[tuple[str, str]]:
    """Return list of (severity, message). severity in {'CRITICAL','WARNING'}."""
    issues: list[tuple[str, str]] = []
    if schema.get("@type") != "BreadcrumbList":
        issues.append(("CRITICAL", "@type must be BreadcrumbList"))
    items = schema.get("itemListElement") or []
    if not items:
        issues.append(("CRITICAL", "itemListElement must not be empty"))
    for i, it in enumerate(items):
        expected = i + 1
        if it.get("position") != expected:
            issues.append(("CRITICAL", f"position[{i}] expected {expected}, got {it.get('position')}"))
        if not it.get("name"):
            issues.append(("CRITICAL", f"item[{i}] missing name"))
        url = it.get("item")
        if url is not None and not str(url).startswith(("http://", "https://")):
            issues.append(("CRITICAL", f"item[{i}].item must be absolute URL"))
        name = it.get("name") or ""
        if len(name) > 128:
            issues.append(("WARNING", f"item[{i}].name longer than 128 chars"))
    return issues


# ---------- React component emission ----------

REACT_TEMPLATE = '''"use client";
import {{ usePathname }} from "next/navigation";
import Script from "next/script";

const SITE = {site_json};
const IN_LANGUAGE = {in_language_json};
const LABELS: Record<string, string> = {labels_json};

function resolveLabel(segPath: string, title?: string): string {{
  const raw = LABELS[segPath];
  if (raw) return raw.includes("{{title}}") ? raw.replace("{{title}}", title ?? "") : raw;
  // dynamic match: /blog/foo against /blog/[slug]
  const parts = segPath.split("/");
  for (const [pattern, value] of Object.entries(LABELS)) {{
    const pp = pattern.split("/");
    if (pp.length !== parts.length) continue;
    const ok = pp.every((p, i) => p === parts[i] || /^\\[(\\.\\.\\.)?\\w+\\]$/.test(p));
    if (ok) return value.includes("{{title}}") ? value.replace("{{title}}", title ?? "") : value;
  }}
  return parts[parts.length - 1] || "Home";
}}

export function BreadcrumbSchema({{ title }}: {{ title?: string }}) {{
  const pathname = usePathname() || "/";
  const segs = pathname === "/" ? [] : pathname.split("/").filter(Boolean);

  const items: Array<Record<string, unknown>> = [
    {{ "@type": "ListItem", position: 1, name: LABELS["/"] ?? "Home", item: `${{SITE}}/` }},
  ];
  let acc = "";
  segs.forEach((seg, i) => {{
    acc = `${{acc}}/${{seg}}`;
    const isLast = i === segs.length - 1;
    const item: Record<string, unknown> = {{
      "@type": "ListItem",
      position: i + 2,
      name: resolveLabel(acc, isLast ? title : undefined),
    }};
    if (!isLast) item.item = `${{SITE}}${{acc}}`;
    items.push(item);
  }});

  const schema = {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    inLanguage: IN_LANGUAGE,
    itemListElement: items,
  }};

  // Escape HTML-sensitive chars in inline JSON-LD to neutralise XSS from
  // untrusted titles (e.g. a slug title containing `</script>` or `<`).
  // Standard pattern recommended by OWASP for inline JSON in HTML.
  const safe = JSON.stringify(schema)
    .replace(/</g, "\\u003c")
    .replace(/>/g, "\\u003e")
    .replace(/&/g, "\\u0026")
    .replace(/\\u2028/g, "\\\\u2028")
    .replace(/\\u2029/g, "\\\\u2029");

  return (
    <Script
      id="breadcrumb-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{{{ __html: safe }}}}
    />
  );
}}
'''


def emit_react(cfg: dict[str, Any]) -> str:
    return REACT_TEMPLATE.format(
        site_json=json.dumps(cfg["site"].rstrip("/")),
        in_language_json=json.dumps(cfg.get("inLanguage", "ja")),
        labels_json=json.dumps(cfg.get("labels", {}), ensure_ascii=False, indent=2),
    )


# ---------- app/ tree scanner ----------

def scan_app_tree(root: str) -> list[str]:
    """Walk an App Router tree and return unique URL paths (with [slug] preserved)."""
    paths: set[str] = set()
    root_path = Path(root)
    for page in root_path.rglob("page.tsx"):
        rel = page.relative_to(root_path).parent
        url_parts: list[str] = []
        for p in rel.parts:
            if GROUP_SEG.match(p) or PARALLEL_SEG.match(p):
                continue
            url_parts.append(p)
        url = "/" + "/".join(url_parts) if url_parts else "/"
        paths.add(url)
    return sorted(paths)


# ---------- CLI ----------

def main() -> int:
    ap = argparse.ArgumentParser(description="BreadcrumbList JSON-LD generator")
    ap.add_argument("--path", help="URL path (e.g. /blog/foo)")
    ap.add_argument("--config", help="YAML config file (site, inLanguage, labels)")
    ap.add_argument("--site", help="Override site origin (e.g. https://example.com)")
    ap.add_argument("--title", help="Title for dynamic [slug] resolution")
    ap.add_argument("--in-language", default=None, help="BCP-47 language tag")
    ap.add_argument("--format", choices=["json", "react", "yaml"], default="json")
    ap.add_argument("--scan", help="Scan an app/ directory and report routes")
    ap.add_argument("--output", help="Output file path (defaults to stdout)")
    ap.add_argument("--strict", action="store_true", help="Fail on warnings")
    args = ap.parse_args()

    cfg: dict[str, Any] = {"site": "", "inLanguage": "ja", "labels": {}}
    if args.config:
        cfg.update(load_config(args.config))
    if args.site:
        cfg["site"] = args.site
    if args.in_language:
        cfg["inLanguage"] = args.in_language

    if args.scan:
        routes = scan_app_tree(args.scan)
        missing = [r for r in routes if r not in cfg["labels"]]
        for r in routes:
            mark = " (missing label)" if r in missing else ""
            print(f"{r}{mark}", file=sys.stderr)
        if args.format == "react":
            out = emit_react(cfg)
        else:
            out = json.dumps({"routes": routes, "missing": missing}, ensure_ascii=False, indent=2)
        return write_output(out, args.output)

    if args.format == "react":
        return write_output(emit_react(cfg), args.output)

    if not args.path:
        ap.error("--path is required when --format=json and --scan is not used")

    schema = build_breadcrumb(
        args.path,
        cfg["site"],
        cfg["labels"],
        in_language=cfg.get("inLanguage", "ja"),
        title=args.title,
    )
    issues = validate(schema)
    for sev, msg in issues:
        print(f"[{sev}] {msg}", file=sys.stderr)
    if any(s == "CRITICAL" for s, _ in issues):
        return 2
    if args.strict and issues:
        return 2

    return write_output(json.dumps(schema, ensure_ascii=False, indent=2), args.output)


def write_output(content: str, path: str | None) -> int:
    if path:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
