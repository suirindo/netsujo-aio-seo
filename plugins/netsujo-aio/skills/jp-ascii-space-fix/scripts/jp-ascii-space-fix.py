#!/usr/bin/env python3
"""jp-ascii-space-fix — detect and remove half-width spaces at ASCII<->CJK boundaries.

Default mode is dry-run. Pass --apply to rewrite files in place.

Examples:
    python3 jp-ascii-space-fix.py --scan .
    python3 jp-ascii-space-fix.py --scan ./docs/ --apply
    python3 jp-ascii-space-fix.py --file README.md --dry-run
    python3 jp-ascii-space-fix.py --git-staged --apply
    python3 jp-ascii-space-fix.py --diff origin/main..HEAD

Exit codes:
    0 — no matches found
    1 — matches found in dry-run mode (use for CI gating)
    2 — error (bad args, missing file, etc.)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

# --- Unicode ranges -------------------------------------------------------

# CJK character class used on both sides of the boundary regex.
# Hiragana (3040-309F), Katakana (30A0-30FF), CJK Unified (4E00-9FFF),
# Halfwidth and Fullwidth Forms (FF00-FFEF).
CJK_CLASS = r"[぀-ヿ一-鿿＀-￯]"

# Left side of boundary: ASCII letters, digits, underscore, and closing punctuation.
ASCII_LEFT_CLASS = r"[A-Za-z0-9_.\)\}\]>]"

# Right side of boundary: ASCII letters, digits, underscore, and opening punctuation.
ASCII_RIGHT_CLASS = r"[A-Za-z0-9_\(\{\[<]"

# Pattern A: ASCII + space + CJK   (e.g. "Next.js は")
PATTERN_ASCII_THEN_CJK = re.compile(rf"({ASCII_LEFT_CLASS}) ({CJK_CLASS})")

# Pattern B: CJK + space + ASCII   (e.g. "を Vercel")
PATTERN_CJK_THEN_ASCII = re.compile(rf"({CJK_CLASS}) ({ASCII_RIGHT_CLASS})")


DEFAULT_INCLUDE_EXTS = {
    ".md", ".mdx", ".tsx", ".ts", ".jsx", ".js",
    ".html", ".htm", ".json", ".txt", ".yaml", ".yml",
}

DEFAULT_EXCLUDE_DIRS = {
    "node_modules", ".next", "dist", "build", ".git",
    ".turbo", ".vercel", "coverage", "out",
}


# --- Data types -----------------------------------------------------------

@dataclass
class Match:
    """A single boundary-space hit."""
    path: Path
    line: int
    column: int
    before: str
    after: str


@dataclass
class FileResult:
    """Aggregated matches for one file."""
    path: Path
    matches: list[Match] = field(default_factory=list)
    rewritten: str | None = None  # Set when --apply runs


# --- Context masking ------------------------------------------------------

def mask_protected_regions(text: str, ext: str) -> str:
    """Return a copy of `text` where protected regions are replaced by a sentinel.

    Protected regions (their content must not be scanned):
        - Markdown fenced code blocks (``` ... ``` or ~~~ ... ~~~)
        - Markdown inline code (`...`)
        - Markdown front-matter (--- ... --- at top)
        - HTML attribute values (inside double or single quotes within a tag)
        - JS/TS comments (// ... and /* ... */)

    The sentinel is the NUL character (\\x00) repeated to preserve byte offsets,
    so downstream line/column calculations remain accurate.
    """
    # TODO: implement protected-region masking. The skeleton below preserves
    # offsets by replacing every character in a protected span with "\x00".
    return text


def strip_markdown_line_prefix(line: str) -> tuple[str, int]:
    """Strip Markdown list/heading/blockquote markers from the start of a line.

    Returns (stripped_line, offset_into_original) so column numbers can be
    rebased to the original line. Examples:
        "- 項目"     -> ("項目", 2)
        "## 見出し"  -> ("見出し", 3)
        ">  引用"    -> ("引用", 3)
    """
    # TODO: implement. The skeleton returns the line unchanged.
    return line, 0


# --- Core scanning --------------------------------------------------------

def find_matches_in_text(text: str, path: Path) -> list[Match]:
    """Find every ASCII<->CJK boundary-space match in `text`.

    Uses `mask_protected_regions` first so code blocks / attributes are skipped.
    Emits both before (with space) and after (without space) snippets so the
    caller can render a diff.
    """
    masked = mask_protected_regions(text, path.suffix)
    matches: list[Match] = []

    for line_idx, line in enumerate(masked.splitlines(), start=1):
        stripped, offset = strip_markdown_line_prefix(line)
        for pattern in (PATTERN_ASCII_THEN_CJK, PATTERN_CJK_THEN_ASCII):
            for m in pattern.finditer(stripped):
                col = m.start() + offset + 1  # 1-based column
                before = m.group(0)
                after = m.group(1) + m.group(2)
                matches.append(Match(path=path, line=line_idx, column=col,
                                     before=before, after=after))
    return matches


def rewrite_text(text: str, path: Path) -> str:
    """Return `text` with all unprotected boundary spaces removed.

    Must respect the same protected-region rules as `find_matches_in_text`,
    so masking is applied, replacements are computed on the masked copy, and
    the rewrite is projected back onto the original buffer.
    """
    # TODO: implement masked rewrite. The skeleton applies the regex globally,
    # which is unsafe for code blocks — production callers must use --dry-run
    # until the masking implementation lands.
    text = PATTERN_ASCII_THEN_CJK.sub(r"\1\2", text)
    text = PATTERN_CJK_THEN_ASCII.sub(r"\1\2", text)
    return text


# --- File discovery -------------------------------------------------------

def iter_files(root: Path, include_exts: set[str],
               exclude_dirs: set[str]) -> Iterator[Path]:
    """Yield files under `root` matching extension and excluded-dir filters."""
    if root.is_file():
        if root.suffix in include_exts:
            yield root
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in include_exts:
            continue
        if any(part in exclude_dirs for part in path.parts):
            continue
        yield path


def git_staged_files() -> list[Path]:
    """Return paths of files in the git index (staged for commit)."""
    out = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        text=True,
    )
    return [Path(line) for line in out.splitlines() if line]


def git_diff_files(rev_range: str) -> list[Path]:
    """Return paths of files changed in the given git range (e.g. origin/main..HEAD)."""
    out = subprocess.check_output(
        ["git", "diff", "--name-only", "--diff-filter=ACM", rev_range],
        text=True,
    )
    return [Path(line) for line in out.splitlines() if line]


# --- Orchestration --------------------------------------------------------

def scan_files(paths: Iterable[Path], apply: bool) -> list[FileResult]:
    """Run detection (and optionally rewrite) over each file."""
    results: list[FileResult] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        matches = find_matches_in_text(text, path)
        if not matches:
            continue
        result = FileResult(path=path, matches=matches)
        if apply:
            new_text = rewrite_text(text, path)
            if new_text != text:
                path.write_text(new_text, encoding="utf-8")
                result.rewritten = new_text
        results.append(result)
    return results


def render_human(results: list[FileResult], applied: bool) -> str:
    """Format results for terminal output."""
    lines: list[str] = []
    total = 0
    for r in results:
        for m in r.matches:
            total += 1
            lines.append(f"{m.path}:{m.line}:{m.column}: "
                         f'"{m.before}" -> "{m.after}"')
    lines.append("---")
    lines.append(f"Files with matches: {len(results)}")
    lines.append(f"Total matches: {total}")
    if not applied and total:
        lines.append("Run with --apply to rewrite.")
    return "\n".join(lines)


def render_json(results: list[FileResult]) -> str:
    """Machine-readable output for CI."""
    payload = [
        {
            "path": str(r.path),
            "matches": [
                {"line": m.line, "column": m.column,
                 "before": m.before, "after": m.after}
                for m in r.matches
            ],
        }
        for r in results
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


# --- CLI ------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="jp-ascii-space-fix",
        description="Detect and remove half-width spaces at ASCII<->CJK boundaries.",
    )
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--scan", type=Path, help="Recurse into directory")
    source.add_argument("--file", type=Path, help="Single file")
    source.add_argument("--git-staged", action="store_true",
                        help="Only files staged for commit")
    source.add_argument("--diff", metavar="RANGE",
                        help="Only files changed in git range (e.g. origin/main..HEAD)")

    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true",
                      help="Rewrite files (default is dry-run)")
    mode.add_argument("--dry-run", action="store_true",
                      help="Force dry-run (default behaviour)")

    p.add_argument("--include", default=",".join(sorted(DEFAULT_INCLUDE_EXTS)),
                   help="Comma-separated list of extensions to include")
    p.add_argument("--exclude", default=",".join(sorted(DEFAULT_EXCLUDE_DIRS)),
                   help="Comma-separated list of directory names to exclude")
    p.add_argument("--json", action="store_true", help="Emit JSON")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI color")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    include_exts = {e if e.startswith(".") else f".{e}"
                    for e in args.include.split(",") if e}
    exclude_dirs = {d for d in args.exclude.split(",") if d}

    if args.scan:
        paths = list(iter_files(args.scan, include_exts, exclude_dirs))
    elif args.file:
        paths = [args.file]
    elif args.git_staged:
        paths = [p for p in git_staged_files() if p.suffix in include_exts]
    elif args.diff:
        paths = [p for p in git_diff_files(args.diff) if p.suffix in include_exts]
    else:  # argparse guarantees one branch fires
        return 2

    results = scan_files(paths, apply=args.apply)

    if args.json:
        print(render_json(results))
    else:
        print(render_human(results, applied=args.apply))

    if not results:
        return 0
    return 0 if args.apply else 1


if __name__ == "__main__":
    sys.exit(main())
