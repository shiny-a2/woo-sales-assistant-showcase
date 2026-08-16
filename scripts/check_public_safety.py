#!/usr/bin/env python3
"""Refuse to publish anything that should not leave the private repository.

This runs before every push. Publishing is the one action in this project that
cannot be undone: a private mistake is a commit to amend, a public one is
already indexed. So the checker is deliberately paranoid and fails closed — an
unreadable file, an unexpected path, or an unknown pattern is a failure, not a
warning.

It reports stable category names and never echoes the offending content, so the
failure output itself cannot become the leak.
"""

import hashlib
import pathlib
import re
import sys
from typing import List, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]

# An allowlist rather than a denylist. A new file is a deliberate decision, not
# something that arrives by accident with a git add -A.
APPROVED_PATHS = frozenset(
    {
        ".gitignore",
        "CHANGELOG.md",
        "README.md",
        "VERSION",
        "scripts/check_public_safety.py",
        "tests/test_public_safety.py",
        ".github/workflows/public-safety.yml",
    }
)

MAX_FILE_BYTES = 256 * 1024
EXPECTED_VERSION = "0.1.0"

SECRET_PATTERNS: Tuple[Tuple[str, "re.Pattern[bytes]"], ...] = (
    ("private-key", re.compile(rb"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")),
    ("certificate", re.compile(rb"-----BEGIN " rb"CERTIFICATE-----")),
    ("aws-access-key", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("generic-secret", re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b")),
    (
        "secret-assignment",
        re.compile(
            rb"(?i)\b(?:password|passwd|client_secret|api[_-]?key|access[_-]?token)"
            rb"\s*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{12,}"
        ),
    ),
)

IPV4 = re.compile(r"(?<![0-9.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9.])")
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
# Iranian mobile numbers, in every form the store's own code accepts.
MOBILE = re.compile(r"(?<![0-9])(?:\+98|0098|0)?9[0-9]{9}(?![0-9])")

# Things that identify this particular client, its infrastructure, or its
# private source. None of them belong in a public engineering write-up.
CLIENT_TERMS = re.compile(
    r"(?i)\b(?:javaheri\w*|kavenegar|snapp\s*pay|snapppay|digikala|torob|"
    r"public_html|cpanel|almalinux|litespeed|memcached|"
    r"wp-config|wp_postmeta|wp_options|a2_ch_\w+|a2_crm_\w+|crmnahayi)\b"
)

# Source code, rather than a description of it.
EMBEDDED_SOURCE = re.compile(
    r"(?m)(?:<\?php|\bwp_ajax_|\badd_action\s*\(|\badd_filter\s*\(|"
    r"\bINSERT\s+INTO\b|\bCREATE\s+TABLE\b|\$wpdb\b)"
)

# A long hex run is either an internal digest or a key. Neither is publishable.
LONG_HEX = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{32,}(?![0-9a-fA-F])")

# example.* are the reserved documentation domains; the other two are this
# project's own public presence. Nothing client-owned is listed, on purpose.
ALLOWED_DOMAINS = frozenset(
    {"example.com", "example.net", "example.org", "example.test", "amiraliyaghouti.com", "github.com"}
)
DOMAIN = re.compile(
    r"(?<![A-Za-z0-9_-])(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"(?:com|net|org|io|dev|ir|co|app|cloud|me)(?![A-Za-z0-9-])"
)


def content_failures(relative: str, data: bytes) -> List[str]:
    failures: List[str] = []

    if len(data) > MAX_FILE_BYTES:
        return ["file-too-large"]

    if b"\x00" in data:
        return ["binary-content"]

    for name, pattern in SECRET_PATTERNS:
        if pattern.search(data) is not None:
            failures.append(name)

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return failures + ["invalid-utf8"]

    if IPV4.search(text) is not None:
        failures.append("ip-address")

    if EMAIL.search(text) is not None:
        failures.append("email-address")

    if MOBILE.search(text) is not None:
        failures.append("mobile-number")

    if relative != "scripts/check_public_safety.py" and CLIENT_TERMS.search(text) is not None:
        failures.append("client-or-infrastructure-identifier")

    # The checker necessarily contains its own patterns; exempting only this file
    # keeps the rule honest everywhere else. The test suite deliberately builds
    # its fixtures from concatenated fragments rather than being exempted, so it
    # can prove each rule without carrying the payload it asserts about.
    if relative != "scripts/check_public_safety.py":
        if EMBEDDED_SOURCE.search(text) is not None:
            failures.append("embedded-source")

        # Pinning a workflow action to a commit is required — an unpinned action
        # is the actual risk — and a commit id is the opposite of a secret. The
        # exemption is therefore scoped to that exact shape in that exact place,
        # not to the file, so any other long hex in a workflow still fails.
        scanned_for_hex = text

        if relative.startswith(".github/workflows/"):
            scanned_for_hex = re.sub(r"uses: \S+@[0-9a-f]{40}\b", "uses: <pinned>", scanned_for_hex)

        if LONG_HEX.search(scanned_for_hex) is not None:
            failures.append("long-hex-digest")

    for match in DOMAIN.finditer(text):
        domain = match.group().lower().rstrip(".")
        if domain not in ALLOWED_DOMAINS:
            failures.append("unapproved-domain")
            break

    return failures


def main() -> int:
    findings: List[str] = []
    seen = set()

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue

        relative = path.relative_to(ROOT).as_posix()

        if relative.startswith(".git/") or "__pycache__" in relative:
            continue

        seen.add(relative)

        if relative not in APPROVED_PATHS:
            findings.append(f"{relative}: unapproved-path")
            continue

        try:
            data = path.read_bytes()
        except OSError:
            findings.append(f"{relative}: unreadable")
            continue

        for failure in content_failures(relative, data):
            findings.append(f"{relative}: {failure}")

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").is_file() else ""

    if version != EXPECTED_VERSION:
        findings.append(f"VERSION: expected {EXPECTED_VERSION}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").is_file() else ""
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8") if (ROOT / "CHANGELOG.md").is_file() else ""

    if EXPECTED_VERSION not in readme or f"[{EXPECTED_VERSION}]" not in changelog:
        findings.append("release-metadata: version not stated in README and CHANGELOG")

    if findings:
        print("public showcase safety scan: FAILED")
        for finding in findings:
            print("  - " + finding)
        return 1

    digest = hashlib.sha256(
        b"".join(sorted((ROOT / p).read_bytes() for p in seen))
    ).hexdigest()[:12]
    print(f"public showcase safety scan: ok ({len(seen)} files, content digest {digest})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
