#!/usr/bin/env python3
"""Schema.org Event JSON-LD generator.

Generates Event structured data with online / offline / hybrid attendance
modes, validates Google rich results requirements (timezone-aware startDate,
location shape per mode, image dimensions), and emits plain JSON, a Next.js
App Router React component, or a Strapi v5 component scaffold.

Battle-tested on miyakodeit.com (155+京都IT勉強会イベント).

CLI examples:
    python3 jsonld-event.py --input event.yaml --output schema.json
    python3 jsonld-event.py --input event.yaml --attendance online \\
        --output EventSchema.tsx --format react
    python3 jsonld-event.py --batch ./events/ --output ./public/jsonld/
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # noqa: N816

AttendanceMode = Literal["online", "offline", "mixed"]
OutputFormat = Literal["json", "react", "strapi"]
EventStatus = Literal[
    "EventScheduled",
    "EventCancelled",
    "EventPostponed",
    "EventRescheduled",
    "EventMovedOnline",
]

ALLOWED_EVENT_STATUS: tuple[str, ...] = (
    "EventScheduled",
    "EventCancelled",
    "EventPostponed",
    "EventRescheduled",
    "EventMovedOnline",
)

ATTENDANCE_MODE_IRI: dict[AttendanceMode, str] = {
    "online": "https://schema.org/OnlineEventAttendanceMode",
    "offline": "https://schema.org/OfflineEventAttendanceMode",
    "mixed": "https://schema.org/MixedEventAttendanceMode",
}

# ISO 8601 with timezone offset (Z or ±HH:MM). Required by Google rich results.
ISO_WITH_TZ = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})$"
)


@dataclass
class ValidationIssue:
    """A single validation finding produced during JSON-LD generation."""

    severity: Literal["critical", "warning"]
    field: str
    message: str


@dataclass
class EventInput:
    """Normalized event input loaded from YAML / JSON / dict.

    Attributes mirror the Schema.org Event vocabulary. Optional fields are
    `None` when omitted; downstream serialization drops `None` values.
    """

    name: str
    start_date: str
    end_date: str | None = None
    description: str | None = None
    image: str | list[str] | None = None
    attendance: AttendanceMode = "offline"
    location: dict[str, Any] = field(default_factory=dict)
    organizer: dict[str, Any] | None = None
    performer: dict[str, Any] | list[dict[str, Any]] | None = None
    offers: dict[str, Any] | list[dict[str, Any]] | None = None
    event_status: EventStatus = "EventScheduled"
    url: str | None = None
    in_language: str | None = None


def load_input(path: Path) -> dict[str, Any]:
    """Load an event description from YAML or JSON.

    Args:
        path: File path. Suffix `.yaml`/`.yml` is parsed as YAML; otherwise JSON.

    Returns:
        Raw dictionary representation of the event.
    """
    # TODO: implement
    raise NotImplementedError


def normalize_input(raw: dict[str, Any], attendance_override: AttendanceMode | None = None) -> EventInput:
    """Normalize a raw dict into an `EventInput` dataclass.

    Resolves attendance mode (CLI override > input field > default `offline`),
    coerces `eventStatus` casing, and fills sensible defaults.

    Args:
        raw: Parsed input dict.
        attendance_override: CLI `--attendance` value, if provided.

    Returns:
        Normalized `EventInput` ready for validation.
    """
    # TODO: implement
    raise NotImplementedError


def build_location(event: EventInput) -> dict[str, Any] | list[dict[str, Any]]:
    """Build the `location` value for the given attendance mode.

    - online → single `VirtualLocation` dict with `url`
    - offline → single `Place` dict with `address` (PostalAddress)
    - mixed → list of `[VirtualLocation, Place]`

    Args:
        event: Normalized event input.

    Returns:
        Schema.org location value, suitable for direct serialization.
    """
    # TODO: implement
    raise NotImplementedError


def build_jsonld(event: EventInput) -> dict[str, Any]:
    """Build the final Event JSON-LD dictionary.

    Assembles `@context`, `@type`, required and recommended fields, and
    `eventAttendanceMode` IRI. Drops fields whose value is `None`.

    Args:
        event: Normalized event input.

    Returns:
        Serializable JSON-LD dictionary.
    """
    # TODO: implement
    raise NotImplementedError


def validate(event: EventInput, jsonld: dict[str, Any]) -> list[ValidationIssue]:
    """Validate the assembled JSON-LD against Google rich results rules.

    Checks (see `references/event-schema-spec.md` for the full matrix):
        - @context / @type / name / startDate / location present
        - startDate matches ISO 8601 with timezone offset
        - endDate >= startDate when both present
        - location shape matches attendance mode
        - OfflineEvent location has no `url`
        - eventStatus in allowed set
        - offers.price and offers.priceCurrency both set or both absent
        - image present (warning if missing or likely < 1200px)

    Args:
        event: Normalized event input.
        jsonld: Output of `build_jsonld`.

    Returns:
        List of validation issues. Empty list means clean.
    """
    # TODO: implement
    raise NotImplementedError


def render_json(jsonld: dict[str, Any]) -> str:
    """Serialize JSON-LD as pretty-printed JSON (UTF-8, no ASCII escaping)."""
    # TODO: implement
    raise NotImplementedError


def render_react(jsonld: dict[str, Any], component_name: str = "EventSchema") -> str:
    """Render a Next.js App Router React component embedding the JSON-LD.

    Uses `next/script` with `type="application/ld+json"`. The component name
    is configurable so callers can host multiple event schemas per page.

    Args:
        jsonld: JSON-LD dictionary to embed.
        component_name: Exported React component identifier.

    Returns:
        TSX source string.
    """
    # TODO: implement
    raise NotImplementedError


def render_strapi(jsonld: dict[str, Any]) -> str:
    """Render a Strapi v5 component schema JSON for Event structured data.

    Produces a `category: event` component with fields aligned to Schema.org
    Event (name, startDate, endDate, attendance, location, organizer, offers).

    Args:
        jsonld: JSON-LD dictionary, used to seed default values.

    Returns:
        JSON string describing the Strapi component.
    """
    # TODO: implement
    raise NotImplementedError


def iter_batch_inputs(directory: Path) -> Iterable[Path]:
    """Yield every `*.yaml` / `*.yml` / `*.json` file in `directory`."""
    # TODO: implement
    raise NotImplementedError


def report_issues(issues: list[ValidationIssue], strict: bool) -> int:
    """Print validation issues and return a process exit code.

    Args:
        issues: Validation findings.
        strict: When True, Warning-level issues also produce a non-zero exit.

    Returns:
        Process exit code: 0 clean, 1 critical, 2 warning under strict mode.
    """
    # TODO: implement
    raise NotImplementedError


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Build the argparse CLI."""
    parser = argparse.ArgumentParser(
        prog="jsonld-event",
        description="Generate Schema.org Event JSON-LD with attendance-mode awareness.",
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", type=Path, help="Path to a single event YAML/JSON file.")
    src.add_argument("--batch", type=Path, help="Directory of event YAML/JSON files.")
    src.add_argument("--connpass-url", type=str, help="connpass event URL (planned; not yet implemented).")

    parser.add_argument("--output", type=Path, required=True, help="Output file or directory.")
    parser.add_argument(
        "--attendance",
        choices=("online", "offline", "mixed"),
        default=None,
        help="Override eventAttendanceMode. Default: read from input or 'offline'.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "react", "strapi"),
        default="json",
        help="Output format. Default: json.",
    )
    parser.add_argument(
        "--status",
        choices=ALLOWED_EVENT_STATUS,
        default=None,
        help="Override eventStatus. Default: read from input or 'EventScheduled'.",
    )
    parser.add_argument(
        "--component-name",
        default="EventSchema",
        help="Exported React component name (only used with --format react).",
    )
    parser.add_argument(
        "--strict",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Treat Warning-level validation issues as failures.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    args = parse_args(argv)

    if args.connpass_url:
        print("--connpass-url is planned but not yet implemented.", file=sys.stderr)
        return 64  # EX_USAGE

    # TODO: implement
    #   1. Load input(s) via load_input / iter_batch_inputs
    #   2. normalize_input(raw, args.attendance)
    #   3. build_jsonld(event)
    #   4. validate(event, jsonld) → report_issues
    #   5. render_json | render_react | render_strapi
    #   6. Write to args.output (file for single, directory for batch)
    raise NotImplementedError


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
