"""Canonical, versioned identity projection and owner-only digest handling."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
from collections.abc import Iterable, Mapping
import unicodedata
import uuid


ASCII_EDGE_WHITESPACE = " \t\n\r\v\f"
V1_DIGEST_LINE = re.compile(rb"[0-9a-f]{64}\n\Z")
V2_DIGEST_LINE = re.compile(rb"v2:[0-9a-f]{64}\n\Z")


def _canonical_string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    normalized = unicodedata.normalize("NFC", value.strip(ASCII_EDGE_WHITESPACE))
    if not normalized or any(unicodedata.category(character) == "Cc" for character in normalized):
        raise ValueError(f"{field} must be a non-empty value without control characters")
    return normalized


def canonical_identity(
    raw: Mapping[str, object], identity_contract: str
) -> dict[str, object]:
    """Project the reviewed Claude surface into its schema-2 public contract."""
    if not isinstance(raw, Mapping) or identity_contract != "claude_auth_status_v1":
        raise ValueError("identity contract is unsupported")
    auth_method = _canonical_string(raw.get("authMethod"), "authMethod")
    subscription_type = _canonical_string(
        raw.get("subscriptionType"), "subscriptionType"
    )
    raw_org_id = _canonical_string(raw.get("orgId"), "orgId")
    try:
        org_id = str(uuid.UUID(raw_org_id))
    except (ValueError, AttributeError) as error:
        raise ValueError("orgId must be a UUID") from error
    return {
        "schema_version": 2,
        "identity_contract": identity_contract,
        "provider": "claude",
        "auth_method": auth_method,
        "org_id": org_id,
        "subscription_type": subscription_type,
    }


def canonical_bytes(raw: Mapping[str, object], identity_contract: str) -> bytes:
    return json.dumps(
        canonical_identity(raw, identity_contract),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def identity_digest(raw: Mapping[str, object], identity_contract: str) -> str:
    return hashlib.sha256(canonical_bytes(raw, identity_contract)).hexdigest()


def digest_line(raw: Mapping[str, object], identity_contract: str) -> bytes:
    return b"v2:" + identity_digest(raw, identity_contract).encode("ascii") + b"\n"


def read_digest_file(path: Path) -> tuple[int, bytes]:
    """Read a v1 or v2 owner-only digest without following symlinks."""
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
            data = stream.read(69)
    finally:
        os.close(descriptor)
    if V1_DIGEST_LINE.fullmatch(data):
        return 1, data
    if V2_DIGEST_LINE.fullmatch(data):
        return 2, data
    raise ValueError("identity digest content is invalid")


def compare_enrolled_identity(
    raw: Mapping[str, object], digest_path: Path, identity_contract: str
) -> str:
    """Return a public state without exposing canonical bytes or either digest."""
    try:
        if not digest_path.exists() and not digest_path.is_symlink():
            return "not_enrolled"
        version, enrolled = read_digest_file(digest_path)
        if version == 1:
            return "stale_enrollment"
        current = digest_line(raw, identity_contract)
    except (OSError, ValueError):
        return "unknown"
    return "matched" if hmac.compare_digest(enrolled, current) else "identity_drift"


def find_duplicate_enrollment(current: bytes, other_paths: Iterable[Path]) -> bool:
    """Compare one v2 digest with reviewed other-profile paths without exposing it."""
    if V2_DIGEST_LINE.fullmatch(current) is None:
        raise ValueError("current identity digest content is invalid")
    for path in other_paths:
        try:
            path.lstat()
        except FileNotFoundError:
            continue
        version, enrolled = read_digest_file(path)
        if version == 1:
            continue
        if hmac.compare_digest(enrolled, current):
            return True
    return False
