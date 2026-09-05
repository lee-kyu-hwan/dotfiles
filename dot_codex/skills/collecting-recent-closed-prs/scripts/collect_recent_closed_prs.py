"""Deterministic primitives for collecting recently closed pull requests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class Interval:
    start_at: str
    end_at: str
    timezone: str
    input_mode: dict[str, object]
    as_of: str
    last_day_partial: bool


def resolve_interval(
    *,
    start_at: str | None,
    end_at: str | None,
    start_date: str | None,
    end_date: str | None,
    recent_days: int | None,
    timezone_name: str,
    as_of: str | None,
) -> Interval:
    """Resolve one requested interval into whole-second UTC bounds."""
    input_timezone = _timezone(timezone_name)
    mode = _interval_mode(start_at, end_at, start_date, end_date, recent_days)

    if mode == "timestamps":
        if as_of is not None:
            raise ValueError("as_of is only valid with recent_days")
        start = _parse_timestamp(start_at, "start_at")
        end = _parse_timestamp(end_at, "end_at")
        input_mode: dict[str, object] = {"start_at": start_at, "end_at": end_at}
        last_day_partial = False
        resolved_as_of = end
    elif mode == "dates":
        if as_of is not None:
            raise ValueError("as_of is only valid with recent_days")
        local_start = _parse_date(start_date, "start_date")
        local_end = _parse_date(end_date, "end_date") + timedelta(days=1)
        start = datetime.combine(local_start, time.min, input_timezone)
        end = datetime.combine(local_end, time.min, input_timezone)
        input_mode = {"start_date": start_date, "end_date": end_date}
        last_day_partial = False
        resolved_as_of = end.astimezone(timezone.utc)
    else:
        if recent_days is None or isinstance(recent_days, bool) or recent_days <= 0:
            raise ValueError("recent_days must be a positive integer")
        current = (
            _parse_timestamp(as_of, "as_of") if as_of is not None else datetime.now(timezone.utc)
        ).astimezone(input_timezone)
        local_start = current.date() - timedelta(days=recent_days - 1)
        start = datetime.combine(local_start, time.min, input_timezone)
        end = current
        input_mode = {"recent_days": recent_days}
        last_day_partial = True
        resolved_as_of = current.astimezone(timezone.utc)

    start = _whole_second(start)
    end = _whole_second(end)
    if start >= end:
        raise ValueError("start_at must be earlier than end_at")

    return Interval(
        start_at=_utc_string(start),
        end_at=_utc_string(end),
        timezone=timezone_name,
        input_mode=input_mode,
        as_of=_utc_string(resolved_as_of),
        last_day_partial=last_day_partial,
    )


def build_closed_query(repository: str, interval: Interval, outcome: str) -> str:
    """Build one Search API qualifier for a UTC half-open closed interval."""
    if outcome not in {"all", "merged", "closed-unmerged"}:
        raise ValueError("outcome must be all, merged, or closed-unmerged")

    start = _parse_timestamp(interval.start_at, "interval.start_at")
    end = _parse_timestamp(interval.end_at, "interval.end_at")
    if start >= end:
        raise ValueError("interval.start_at must be earlier than interval.end_at")

    qualifiers = [
        f"repo:{repository}",
        "is:pr",
        "is:closed",
        f"closed:{_utc_string(start)}..{_utc_string(end - timedelta(seconds=1))}",
    ]
    if outcome == "merged":
        qualifiers.append("is:merged")
    elif outcome == "closed-unmerged":
        qualifiers.append("-is:merged")
    return " ".join(qualifiers)


def migrate_manifest_v1(document: dict[str, object]) -> dict[str, object]:
    """Project a v1 fixture manifest into the v2 envelope without data loss."""
    if document.get("schema_version") != "1.0.0":
        raise ValueError("only manifest schema_version 1.0.0 can be migrated")

    legacy_document = deepcopy(document)
    legacy_runs = legacy_document.pop("runs", None)
    if not isinstance(legacy_runs, list):
        raise ValueError("manifest 1.0.0 runs must be a list")

    generated_by = legacy_document.pop("generated_by", None)
    legacy_document.pop("schema_version")
    records = [_migrate_run(run) for run in legacy_runs]
    migrated: dict[str, object] = {
        "schema_version": "2.0.0",
        "generated_by": generated_by,
        "records": records,
    }
    if legacy_document:
        migrated["legacy_payload"] = legacy_document
    return migrated


def _migrate_run(run: object) -> dict[str, object]:
    if not isinstance(run, dict):
        raise ValueError("manifest 1.0.0 runs must contain objects")

    legacy_run = deepcopy(run)
    record: dict[str, object] = {
        "run_id": legacy_run.pop("run_key", None),
        "collection_method": legacy_run.pop("kind", None),
        "completed_at": legacy_run.pop("captured_at", None),
        "api_version": legacy_run.pop("github_api_version", None),
        "client_version": legacy_run.pop("github_cli_version", None),
        "started_at": None,
        "collection_status": "partial",
        "migration_warnings": [
            "Legacy manifest has no start time, request fingerprint, or canonical completeness result; migrated run is partial."
        ],
    }
    if "warnings" in legacy_run:
        record["warnings"] = legacy_run.pop("warnings")
    if legacy_run:
        record["legacy_payload"] = legacy_run
    return record


def _timezone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, TypeError) as error:
        raise ValueError(f"invalid timezone: {timezone_name}") from error


def _interval_mode(
    start_at: str | None,
    end_at: str | None,
    start_date: str | None,
    end_date: str | None,
    recent_days: int | None,
) -> str:
    timestamps_supplied = start_at is not None or end_at is not None
    dates_supplied = start_date is not None or end_date is not None
    complete_modes = [
        start_at is not None and end_at is not None,
        start_date is not None and end_date is not None,
        recent_days is not None,
    ]
    if sum(complete_modes) != 1 or (timestamps_supplied and not complete_modes[0]) or (
        dates_supplied and not complete_modes[1]
    ):
        raise ValueError("select exactly one complete interval mode")
    return ("timestamps", "dates", "recent_days")[complete_modes.index(True)]


def _parse_timestamp(value: str | None, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an RFC 3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field} must be an RFC 3339 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone offset")
    return _whole_second(parsed).astimezone(timezone.utc)


def _parse_date(value: str | None, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO 8601 date")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO 8601 date") from error


def _whole_second(value: datetime) -> datetime:
    return value.replace(microsecond=0)


def _utc_string(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
