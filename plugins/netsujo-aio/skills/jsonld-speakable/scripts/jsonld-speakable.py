#!/usr/bin/env python3
"""
jsonld-speakable.py — Generate and verify WebPage + SpeakableSpecification JSON-LD.

Usage:
    python3 jsonld-speakable.py --config speakable.yaml --url https://example.com/about --output schema.json
    python3 jsonld-speakable.py --config speakable.yaml --output SpeakableSchema.tsx --format react
    python3 jsonld-speakable.py --verify --url https://example.com/about --llms-txt public/llms.txt
    python3 jsonld-speakable.py --config speakable.yaml --url https://example.com/about --scan-html

This is a skeleton. Fill in TODO sections as the netsujo-aio plugin evolves.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore

try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:
    BeautifulSoup = None  # type: ignore


SCHEMA_CONTEXT = "https://schema.org"
DEFAULT_LANG = "ja"
MARKETING_FLUFF_TOKENS = (
    "情熱",
    "圧倒的",
    "唯一無二",
    "革命的",
    "最高峰",
    "world-class",
    "best-in-class",
    "revolutionary",
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class SpeakableConfig:
    url: str
    name: str | None = None
    description: str | None = None
    in_language: str = DEFAULT_LANG
    css_selector: list[str] = field(default_factory=list)
    xpath: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> "SpeakableConfig":
        if yaml is None:
            raise RuntimeError("PyYAML is required. Install with: pip install pyyaml")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        speakable = data.get("speakable", {}) or {}
        return cls(
            url=data.get("url", ""),
            name=data.get("name"),
            description=data.get("description"),
            in_language=data.get("inLanguage", DEFAULT_LANG),
            css_selector=list(speakable.get("cssSelector", []) or []),
            xpath=list(speakable.get("xpath", []) or []),
        )


@dataclass
class ValidationIssue:
    severity: str  # "critical" | "warning"
    message: str


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_config(cfg: SpeakableConfig) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not cfg.url:
        issues.append(ValidationIssue("critical", "url is required"))

    if cfg.css_selector and cfg.xpath:
        issues.append(
            ValidationIssue(
                "critical",
                "speakable must use cssSelector OR xpath, not both",
            )
        )

    if not cfg.css_selector and not cfg.xpath:
        issues.append(
            ValidationIssue(
                "critical",
                "speakable requires at least one cssSelector or xpath entry",
            )
        )

    if not re.fullmatch(r"[A-Za-z]{2,3}(-[A-Za-z0-9]{1,8})*", cfg.in_language):
        issues.append(
            ValidationIssue("warning", f"inLanguage '{cfg.in_language}' is not BCP-47")
        )

    return issues


def validate_passages(passages: list[str], lang: str) -> list[ValidationIssue]:
    """Length and fluff checks for the text behind each selector."""
    issues: list[ValidationIssue] = []
    for text in passages:
        length = len(text)
        if lang.startswith("ja"):
            lo, hi = 30, 200
        else:
            lo, hi = 80, 400
        if length < lo:
            issues.append(
                ValidationIssue(
                    "warning",
                    f"passage too short ({length} chars, expected >={lo}): {text[:40]}...",
                )
            )
        elif length > hi:
            issues.append(
                ValidationIssue(
                    "warning",
                    f"passage too long ({length} chars, expected <={hi}): {text[:40]}...",
                )
            )
        for token in MARKETING_FLUFF_TOKENS:
            if token in text:
                issues.append(
                    ValidationIssue(
                        "warning",
                        f"marketing fluff token '{token}' in speakable passage",
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Schema build
# ---------------------------------------------------------------------------


def build_schema(cfg: SpeakableConfig) -> dict[str, Any]:
    speakable: dict[str, Any] = {"@type": "SpeakableSpecification"}
    if cfg.css_selector:
        speakable["cssSelector"] = cfg.css_selector
    if cfg.xpath:
        speakable["xpath"] = cfg.xpath

    schema: dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "WebPage",
        "url": cfg.url,
        "inLanguage": cfg.in_language,
        "speakable": speakable,
    }
    if cfg.name:
        schema["name"] = cfg.name
    if cfg.description:
        schema["description"] = cfg.description
    return schema


# ---------------------------------------------------------------------------
# HTML scan
# ---------------------------------------------------------------------------


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": "netsujo-aio-speakable/1.0"})
    with urlopen(req, timeout=30) as resp:  # noqa: S310
        return resp.read().decode("utf-8", errors="replace")


def extract_passages(html: str, selectors: list[str]) -> dict[str, list[str]]:
    """Return {selector: [text, ...]}. Requires BeautifulSoup."""
    if BeautifulSoup is None:
        raise RuntimeError("beautifulsoup4 is required for --scan-html / --verify")
    soup = BeautifulSoup(html, "html.parser")
    out: dict[str, list[str]] = {}
    for sel in selectors:
        nodes = soup.select(sel)
        out[sel] = [n.get_text(strip=True) for n in nodes]
    return out


# ---------------------------------------------------------------------------
# llms.txt verify
# ---------------------------------------------------------------------------


def load_llms_txt(path: Path) -> list[str]:
    """Return non-empty, non-heading lines as candidate definition strings."""
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        lines.append(line)
    return lines


def verify_consistency(
    page_passages: list[str], llms_lines: list[str]
) -> tuple[int, list[str]]:
    matched = 0
    mismatches: list[str] = []
    llms_set = set(llms_lines)
    for text in page_passages:
        if text in llms_set:
            matched += 1
        else:
            mismatches.append(text)
    return matched, mismatches


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------


def render_json(schema: dict[str, Any]) -> str:
    return json.dumps(schema, ensure_ascii=False, indent=2)


def render_react(schema: dict[str, Any], component_name: str = "SpeakableSchema") -> str:
    body = json.dumps(schema, ensure_ascii=False, indent=2)
    return f'''import Script from "next/script"

export function {component_name}() {{
  return (
    <Script
      id="speakable-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{{{
        __html: JSON.stringify({body}),
      }}}}
    />
  )
}}
'''


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate and verify WebPage + SpeakableSpecification JSON-LD."
    )
    p.add_argument("--config", type=Path, help="YAML config path")
    p.add_argument("--url", help="Page URL (overrides config.url)")
    p.add_argument("--output", type=Path, help="Output file (default: stdout)")
    p.add_argument(
        "--format",
        choices=["json", "react", "yaml"],
        default="json",
        help="Output format",
    )
    p.add_argument(
        "--scan-html",
        action="store_true",
        help="Fetch --url and confirm every cssSelector resolves",
    )
    p.add_argument(
        "--verify",
        action="store_true",
        help="Verify llms.txt consistency mode",
    )
    p.add_argument("--llms-txt", type=Path, help="llms.txt path for --verify")
    p.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Fail on Warning level issues (default: true)",
    )
    return p


def report_issues(issues: list[ValidationIssue], strict: bool) -> bool:
    """Print issues. Return True if execution should abort."""
    critical = [i for i in issues if i.severity == "critical"]
    warnings = [i for i in issues if i.severity == "warning"]
    for i in critical:
        print(f"[CRITICAL] {i.message}", file=sys.stderr)
    for i in warnings:
        print(f"[WARNING]  {i.message}", file=sys.stderr)
    if critical:
        return True
    if warnings and strict:
        return True
    return False


def cmd_verify(args: argparse.Namespace) -> int:
    if not args.url or not args.llms_txt:
        print("--verify requires --url and --llms-txt", file=sys.stderr)
        return 2
    if not args.config:
        print("--verify requires --config to know which selectors to read", file=sys.stderr)
        return 2

    cfg = SpeakableConfig.from_yaml(args.config)
    cfg.url = args.url or cfg.url
    html = fetch_html(cfg.url)
    selector_map = extract_passages(html, cfg.css_selector)
    page_passages = [t for texts in selector_map.values() for t in texts if t]

    llms_lines = load_llms_txt(args.llms_txt)
    matched, mismatches = verify_consistency(page_passages, llms_lines)

    print(f"Speakable selectors resolved: {sum(1 for v in selector_map.values() if v)}")
    print(f"Speakable passages extracted: {len(page_passages)}")
    print(f"llms.txt definitions matched: {matched} / {len(page_passages)}")

    for text in mismatches:
        print(f"MISMATCH: page text not in llms.txt: {text[:80]}")

    return 0 if not mismatches else 1


def cmd_generate(args: argparse.Namespace) -> int:
    if not args.config:
        print("--config is required", file=sys.stderr)
        return 2

    cfg = SpeakableConfig.from_yaml(args.config)
    if args.url:
        cfg.url = args.url

    issues = validate_config(cfg)

    if args.scan_html:
        html = fetch_html(cfg.url)
        selector_map = extract_passages(html, cfg.css_selector)
        for sel, texts in selector_map.items():
            if not texts:
                issues.append(
                    ValidationIssue(
                        "critical",
                        f"cssSelector '{sel}' resolved to 0 nodes on {cfg.url}",
                    )
                )
        passages = [t for texts in selector_map.values() for t in texts if t]
        issues.extend(validate_passages(passages, cfg.in_language))

    if report_issues(issues, strict=args.strict):
        return 1

    schema = build_schema(cfg)

    if args.format == "json":
        rendered = render_json(schema)
    elif args.format == "react":
        rendered = render_react(schema)
    elif args.format == "yaml":
        if yaml is None:
            print("PyYAML required for --format yaml", file=sys.stderr)
            return 2
        rendered = yaml.safe_dump(schema, allow_unicode=True, sort_keys=False)
    else:
        rendered = render_json(schema)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(rendered)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.verify:
        return cmd_verify(args)
    return cmd_generate(args)


if __name__ == "__main__":
    sys.exit(main())
