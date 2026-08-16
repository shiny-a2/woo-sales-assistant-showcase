#!/usr/bin/env python3
"""Prove the publication guard would actually stop a leak.

A safety checker that passes on clean content proves nothing on its own — the
identity work in this project turned up two guards that were green while testing
nothing at all. So every rule below is exercised against content that should
fail it, and the test fails if the checker lets it through.
"""

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_public_safety", ROOT / "scripts" / "check_public_safety.py"
)
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CHECKER)

# A file name that is on the approved list, so each case tests the content rule
# rather than tripping the path rule by accident.
APPROVED = "README.md"


class PublicSafetyTests(unittest.TestCase):
    def assert_flags(self, content: str, expected: str, message: str) -> None:
        failures = CHECKER.content_failures(APPROVED, content.encode("utf-8"))
        self.assertIn(expected, failures, message)

    def test_clean_content_passes(self) -> None:
        self.assertEqual(
            [],
            CHECKER.content_failures(APPROVED, b"A description of engineering work.\n"),
            "ordinary prose must not be flagged, or the guard becomes noise people ignore",
        )

    def test_credentials_are_refused(self) -> None:
        self.assert_flags(
            "-----BEGIN " + "RSA PRIVATE KEY" + "-----\nMIIE\n", "private-key", "a private key is refused"
        )
        self.assert_flags("AKIA" + "IOSFODNN7EXAMPLE", "aws-access-key", "an access key is refused")
        self.assert_flags(
            "api" + "_key = " + "'abcdefghijklmnop'", "secret-assignment", "an assigned secret is refused"
        )

    def test_personal_and_infrastructure_data_is_refused(self) -> None:
        # Assembled from parts so this test file does not itself carry the values
        # it is asserting about.
        self.assert_flags(".".join(["203", "0", "113", "7"]), "ip-address", "a server address is refused")
        self.assert_flags("someone" + "@" + "example.net", "email-address", "an email address is refused")
        self.assert_flags("0" + "912" + "3456789", "mobile-number", "a customer mobile is refused")

    def test_client_identifiers_are_refused(self) -> None:
        for term, label in (
            ("the " + "javaher" + "ian store", "client name"),
            ("sent through " + "Kaven" + "egar", "SMS provider"),
            ("the " + "Snapp" + "Pay gateway", "payment provider"),
            ("under " + "public" + "_html", "server path"),
            ("a2" + "_ch_" + "points_ledger", "private table name"),
            ("wp" + "-config" + " settings", "site configuration"),
        ):
            with self.subTest(term=label):
                self.assert_flags(
                    term, "client-or-infrastructure-identifier", f"{label} is refused"
                )

    def test_private_source_is_refused(self) -> None:
        for snippet, label in (
            ("<" + "?php echo 1;", "php source"),
            ("add" + "_action" + "('init', 'x');", "hook registration"),
            ("wp" + "_ajax_" + "a2_thing", "ajax endpoint name"),
            ("CREATE" + " TABLE loyalty (", "schema"),
            ("$wp" + "db->query($sql);", "database access"),
        ):
            with self.subTest(term=label):
                self.assert_flags(snippet, "embedded-source", f"{label} is refused")

    def test_internal_digests_are_refused(self) -> None:
        self.assert_flags("f" * 64, "long-hex-digest", "an internal digest is refused")

    def test_unapproved_domains_are_refused(self) -> None:
        self.assert_flags("visit some-shop" + ".ir today", "unapproved-domain", "an unlisted domain is refused")
        self.assertEqual(
            [],
            CHECKER.content_failures(APPROVED, b"see https://github.com/ for the code\n"),
            "an explicitly allowed domain passes",
        )

    def test_the_checker_exempts_only_itself(self) -> None:
        # The checker has to contain its own patterns. That exemption is the one
        # hole in the rule, so it is pinned: it must apply to exactly one file.
        pattern_bearing = "CREATE" + " TABLE x (" + "\n" + "a" * 32
        self.assertIn(
            "embedded-source",
            CHECKER.content_failures("README.md", pattern_bearing.encode("utf-8")),
            "an ordinary file carrying source is refused",
        )
        self.assertNotIn(
            "embedded-source",
            CHECKER.content_failures(
                "scripts/check_public_safety.py", pattern_bearing.encode("utf-8")
            ),
            "only the checker itself is exempt",
        )

    def test_the_checker_exemption_covers_only_its_own_patterns(self) -> None:
        # The checker is exempt because it must contain the terms it searches
        # for. That exemption must not become a place to hide anything else.
        for content, rule in (
            ("-----BEGIN " + "RSA PRIVATE KEY" + "-----\nMIIE\n", "private-key"),
            ("AKIA" + "IOSFODNN7EXAMPLE", "aws-access-key"),
            (".".join(["203", "0", "113", "7"]), "ip-address"),
            ("0" + "912" + "3456789", "mobile-number"),
        ):
            with self.subTest(rule=rule):
                self.assertIn(
                    rule,
                    CHECKER.content_failures(
                        "scripts/check_public_safety.py", content.encode("utf-8")
                    ),
                    f"{rule} is still refused inside the checker itself",
                )

    def test_workflow_hex_exemption_is_scoped_to_a_pinned_action(self) -> None:
        # Pinning an action to a commit is required, and a commit id is the
        # opposite of a secret. The exemption is scoped to that exact shape so a
        # workflow cannot become a hiding place for anything else.
        pinned = "      - uses: actions/checkout@" + "a" * 40 + "\n"
        self.assertEqual(
            [],
            CHECKER.content_failures(".github/workflows/x.yml", pinned.encode("utf-8")),
            "a pinned action commit is allowed in a workflow",
        )

        bare = "      key: " + "a" * 40 + "\n"
        self.assertIn(
            "long-hex-digest",
            CHECKER.content_failures(".github/workflows/x.yml", bare.encode("utf-8")),
            "any other long hex in a workflow is still refused",
        )
        self.assertIn(
            "long-hex-digest",
            CHECKER.content_failures("README.md", pinned.encode("utf-8")),
            "the exemption does not apply outside a workflow file",
        )

    def test_the_approved_path_list_is_closed(self) -> None:
        # A denylist would let a new file arrive unnoticed with `git add -A`.
        self.assertNotIn("docs/notes.md", CHECKER.APPROVED_PATHS, "the list is an allowlist")
        self.assertTrue(
            all(not p.startswith("/") for p in CHECKER.APPROVED_PATHS),
            "approved paths are repository-relative",
        )

    def test_oversized_and_binary_content_is_refused(self) -> None:
        self.assertEqual(
            ["file-too-large"],
            CHECKER.content_failures(APPROVED, b"x" * (CHECKER.MAX_FILE_BYTES + 1)),
            "an oversized file is refused rather than scanned",
        )
        self.assertEqual(
            ["binary-content"],
            CHECKER.content_failures(APPROVED, b"abc\x00def"),
            "binary content is refused, since it cannot be reviewed by reading",
        )


if __name__ == "__main__":
    unittest.main()
