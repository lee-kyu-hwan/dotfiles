"""Shared, non-disclosing identity canonicalization for ai-session helpers."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
import unicodedata
from typing import Mapping


ASCII_EDGE_WHITESPACE = " \t\n\r\v\f"
DIGEST_LINE = re.compile(rb"[0-9a-f]{64}\n\Z")


def _canonical_string(value: object, field: str, *, lowercase: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    normalized = unicodedata.normalize("NFC", value.strip(ASCII_EDGE_WHITESPACE))
    if not normalized or any(unicodedata.category(character) == "Cc" for character in normalized):
        raise ValueError(f"{field} must be a non-empty value without control characters")
    return normalized.lower() if lowercase else normalized


def canonical_identity(raw: Mapping[str, object]) -> dict[str, object]:
    """Project official stable fields into the versioned canonical identity."""
    if not isinstance(raw, Mapping):
        raise ValueError("identity must be an object")
    provider = _canonical_string(raw.get("provider"), "provider", lowercase=True)
    auth_kind = _canonical_string(raw.get("auth_kind"), "auth_kind", lowercase=True)
    if provider not in {"codex", "claude"}:
        raise ValueError("provider is unsupported")
    if auth_kind not in {"consumer", "organization", "api_payg"}:
        raise ValueError("auth_kind is unsupported")
    canonical: dict[str, object] = {
        "schema_version": 1,
        "provider": provider,
        "auth_kind": auth_kind,
        "subject_id": _canonical_string(raw.get("subject_id"), "subject_id"),
    }
    if auth_kind == "organization":
        canonical["tenant_id"] = _canonical_string(raw.get("tenant_id"), "tenant_id")
    return canonical


def canonical_bytes(raw: Mapping[str, object]) -> bytes:
    return json.dumps(
        canonical_identity(raw),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def identity_digest(raw: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_bytes(raw)).hexdigest()


def digest_line(raw: Mapping[str, object]) -> bytes:
    return identity_digest(raw).encode("ascii") + b"\n"


def read_digest_file(path: Path) -> bytes:
    """Read an owner-only enrolled digest without following a symlink."""
    directory = path.parent.lstat()
    if (
        stat.S_ISLNK(directory.st_mode)
        or not stat.S_ISDIR(directory.st_mode)
        or directory.st_uid != os.getuid()
        or stat.S_IMODE(directory.st_mode) != 0o700
    ):
        raise ValueError("identity digest directory owner or mode is invalid")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("identity digest is not a regular file")
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o600:
            raise ValueError("identity digest owner or mode is invalid")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            data = stream.read(66)
    finally:
        os.close(descriptor)
    if not DIGEST_LINE.fullmatch(data):
        raise ValueError("identity digest content is invalid")
    return data


def compare_enrolled_identity(raw: Mapping[str, object], digest_path: Path) -> str:
    """Return only a public verifier state; never return either digest."""
    try:
        enrolled = read_digest_file(digest_path)
        current = digest_line(raw)
    except (OSError, ValueError):
        return "unknown"
    return "matched" if hmac.compare_digest(enrolled, current) else "identity_drift"
