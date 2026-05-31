#!/usr/bin/env python3
"""h1-mobile-check — detect Japanese H1/H2 mobile line-break issues at 375px.

This script combines three layers:

1. Static analysis — extract H1/H2 from .tsx/.jsx/.html/.md/.mdx files or live URLs
   and check character length plus sub-title concatenation patterns.
2. Grammar analysis — detect particle-first lines (を/が/に/で/と/は/から/まで/より/へ/の)
   and verb stem/ending splits using a dictionary of common Japanese verbs.
3. Dynamic analysis — render the target page at 375x667 with Playwright and read
   each line box via getBoundingClientRect() to catch real-world wraps that
   static analysis cannot predict (font fallback, kerning, custom widths).

Playwright is an optional dependency. When unavailable, the script falls back
to static + grammar checks which already catch the three known production
incidents on netsujo.jp and miyakodeit.com.

Usage examples are documented in ../SKILL.md.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# --- Constants -----------------------------------------------------------------

# Japanese particles that must never start a wrapped line (gyoutou kinsoku).
# Source: JIS X 4051 行頭禁則 + netsujo CLAUDE.md style guide.
HEAD_BAN_PARTICLES: tuple[str, ...] = (
    "を", "が", "に", "で", "と", "は", "から", "まで", "より", "へ", "の",
    "や", "も", "ね", "よ", "わ", "か",
)

# Characters that must never end a wrapped line (gyoumatsu kinsoku).
TAIL_BAN_CHARS: tuple[str, ...] = ("「", "『", "（", "【", "［", "〈", "《")

# Common Japanese verb stems whose endings should not be split across lines.
# Keyed by stem, value is the set of inflected endings.
VERB_SPLIT_DICT: dict[str, tuple[str, ...]] = {
    "もたら": ("す", "した", "して", "される"),
    "はじま": ("る", "った", "って"),
    "つく": ("る", "った", "って", "られる"),
    "う": ("ける", "けた"),
}

DEFAULT_MAX_CHARS: int = 15
DEFAULT_MIN_TAIL_CHARS: int = 3
DEFAULT_VIEWPORT: tuple[int, int] = (375, 667)


# --- Data classes --------------------------------------------------------------


@dataclass
class Finding:
    """Single check result for one H1/H2 occurrence."""

    severity: str  # "Critical" | "Warning" | "Info"
    rule: str
    text: str
    location: str  # file:line or URL
    suggestion: str | None = None


@dataclass
class CheckResult:
    """Aggregate of findings for one heading."""

    heading: str
    char_count: int
    location: str
    findings: list[Finding] = field(default_factory=list)
    measured_lines: list[str] | None = None  # set when Playwright runs


# --- Static extraction ---------------------------------------------------------


H1_TAG_REGEX = re.compile(
    r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL
)
H2_TAG_REGEX = re.compile(
    r"<h2[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL
)
JSX_TAG_REGEX = re.compile(
    r"<(h1|h2)[^>]*>\{?([^<{}]+)\}?</\1>", re.IGNORECASE
)
MD_H1_REGEX = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def extract_headings_from_file(path: Path) -> list[tuple[str, str]]:
    """Return [(heading_text, location)] for every H1/H2 in the file.

    Supports .tsx, .jsx, .html, .md, .mdx. Strips JSX expressions inside the
    tag conservatively: anything inside {...} is removed so that we measure
    the static literal portion only.
    """
    # TODO: implement full AST extraction for .tsx (currently regex-only)
    raise NotImplementedError


def strip_html(text: str) -> str:
    """Strip nested tags (e.g. <br />, <span>) and decode HTML entities."""
    # TODO: implement
    raise NotImplementedError


# --- Length & sub-title checks -------------------------------------------------


def check_length(heading: str, max_chars: int = DEFAULT_MAX_CHARS) -> Finding | None:
    """Return a Warning if heading exceeds max_chars (visible character count).

    Counts grapheme clusters, not code points — surrogate pairs and combining
    marks count as one character.
    """
    # TODO: implement grapheme-aware count
    raise NotImplementedError


def check_subtitle_concat(heading: str) -> Finding | None:
    """Flag H1 that concatenates a sub-title with `—`, `:`, `｜`, or `・`.

    Sub-titles should live in a separate <p>, never inside H1.
    """
    # TODO: implement
    raise NotImplementedError


# --- Grammar checks ------------------------------------------------------------


def check_particle_head(lines: Iterable[str]) -> list[Finding]:
    """Flag Critical when any non-first line starts with a banned particle."""
    # TODO: implement
    raise NotImplementedError


def check_verb_split(lines: Iterable[str]) -> list[Finding]:
    """Flag Warning when a verb stem ends one line and its ending starts next."""
    # TODO: implement using VERB_SPLIT_DICT
    raise NotImplementedError


def check_tail_orphan(
    lines: list[str], min_tail: int = DEFAULT_MIN_TAIL_CHARS
) -> Finding | None:
    """Flag Critical when the final wrapped line has fewer than min_tail chars."""
    # TODO: implement
    raise NotImplementedError


# --- Bunsetsu segmentation & <br /> suggestion ---------------------------------


def segment_bunsetsu(heading: str) -> list[str]:
    """Split heading into bunsetsu (文節) — minimal meaning-bearing chunks.

    Heuristic: each bunsetsu is a content word optionally followed by particles
    or auxiliary verbs. Returns the list of chunks in order. We use a simple
    rule-based segmenter rather than a full morphological analyzer to avoid the
    MeCab/Sudachi dependency. This is sufficient for headline-length input.
    """
    # TODO: implement — see ../references/japanese-line-break-rules.md
    raise NotImplementedError


def suggest_break(
    heading: str, max_chars: int = DEFAULT_MAX_CHARS
) -> list[tuple[str, str, tuple[int, int]]]:
    """Return ranked <br /> insertion candidates.

    Each tuple is (left_half, right_half, (left_len, right_len)). Candidates are
    ranked by:

    1. Both halves <= max_chars (hard constraint)
    2. Neither half starts with a particle (hard constraint)
    3. Balance — abs(left_len - right_len) minimized
    4. Bunsetsu boundary preferred over arbitrary cut

    Returns up to 3 candidates, best first. Empty list if no clean break exists.
    """
    # TODO: implement
    raise NotImplementedError


# --- Dynamic measurement (Playwright) ------------------------------------------


def measure_lines_at_viewport(
    url: str, viewport: tuple[int, int] = DEFAULT_VIEWPORT
) -> list[list[str]]:
    """Render url at viewport and return the wrapped lines for every H1/H2.

    Implementation outline (when Playwright is installed):
      1. launch chromium headless with the given viewport
      2. goto(url), wait_for_load_state("domcontentloaded")
      3. evaluate JS that walks document.querySelectorAll("h1, h2"), uses
         document.caretRangeFromPoint or Range API to split textContent into
         lines based on getClientRects(), returns array of arrays
      4. close browser

    Returns [] when Playwright is unavailable; callers must handle that.
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore  # noqa: F401
    except ImportError:
        return []
    # TODO: implement
    raise NotImplementedError


# --- Runner --------------------------------------------------------------------


def check_heading(
    heading: str,
    location: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    measured_lines: list[str] | None = None,
) -> CheckResult:
    """Run all applicable checks on a single heading and return aggregated result."""
    # TODO: orchestrate the individual check_* functions and collect findings
    raise NotImplementedError


def run_url(url: str, max_chars: int, viewport: tuple[int, int]) -> list[CheckResult]:
    """Check every H1/H2 on a live URL with dynamic measurement when possible."""
    # TODO: implement
    raise NotImplementedError


def run_file(path: Path, max_chars: int) -> list[CheckResult]:
    """Static-only check for one source file."""
    # TODO: implement
    raise NotImplementedError


def run_batch(root: Path, max_chars: int) -> list[CheckResult]:
    """Recursively scan root for .tsx/.jsx/.html/.md/.mdx and check each."""
    # TODO: implement
    raise NotImplementedError


# --- Reporting -----------------------------------------------------------------


def render_console(results: list[CheckResult]) -> str:
    """Render a colored console table grouped by location."""
    # TODO: implement
    raise NotImplementedError


def render_markdown(results: list[CheckResult]) -> str:
    """Render a Markdown report suitable for PR descriptions."""
    # TODO: implement
    raise NotImplementedError


def exit_code_for(results: list[CheckResult], strict: bool) -> int:
    """0 clean, 1 Warning only, 2 Critical present (or any in strict mode)."""
    has_critical = any(
        f.severity == "Critical" for r in results for f in r.findings
    )
    has_warning = any(
        f.severity == "Warning" for r in results for f in r.findings
    )
    if has_critical:
        return 2
    if has_warning:
        return 1 if not strict else 2
    return 0


# --- CLI -----------------------------------------------------------------------


def parse_viewport(value: str) -> tuple[int, int]:
    """Parse '375x667' style viewport string."""
    match = re.fullmatch(r"(\d+)x(\d+)", value)
    if not match:
        raise argparse.ArgumentTypeError(f"invalid viewport: {value}")
    return int(match.group(1)), int(match.group(2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="h1-mobile-check",
        description="Detect Japanese H1/H2 mobile line-break issues at 375px.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="live page URL to check")
    group.add_argument("--file", help="source file (.tsx/.jsx/.html/.md/.mdx)")
    group.add_argument("--batch", help="directory to recursively scan")
    group.add_argument("--suggest", help="raw heading string for <br /> suggestion")

    parser.add_argument(
        "--viewport",
        type=parse_viewport,
        default=DEFAULT_VIEWPORT,
        help="viewport WxH (default 375x667)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help=f"H1 length warning threshold (default {DEFAULT_MAX_CHARS})",
    )
    parser.add_argument("--report", help="write markdown report to this path")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero on Warning, not just Critical",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.suggest:
        # TODO: print ranked candidates from suggest_break(args.suggest, args.max_chars)
        raise NotImplementedError

    results: list[CheckResult] = []
    if args.url:
        results = run_url(args.url, args.max_chars, args.viewport)
    elif args.file:
        results = run_file(Path(args.file), args.max_chars)
    elif args.batch:
        results = run_batch(Path(args.batch), args.max_chars)

    print(render_console(results))
    if args.report:
        Path(args.report).write_text(render_markdown(results), encoding="utf-8")

    return exit_code_for(results, args.strict)


if __name__ == "__main__":
    sys.exit(main())
