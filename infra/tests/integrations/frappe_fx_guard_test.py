"""Offline boundary tests for the proposed Frappe before-submit hook."""

import importlib.util
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "frappe_fx_guard",
    Path(__file__).resolve().parents[2] / "scripts/sync/frappe_fx_guard.py",
)
assert spec is not None and spec.loader is not None
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 8, 12, tzinfo=UTC)
        self.row = {
            "base_currency": "USD",
            "quote_currency": "THB",
            "rate": "35.125",
            "quality": "verified",
            "source_type": "reference",
            "source_ref": "fixture",
            "reviewed_by": "fixture-reviewer",
            "as_of": "2026-09-08T11:00:00Z",
            "captured_at": "2026-09-08T11:01:00Z",
            "reviewed_at": "2026-09-08T11:02:00Z",
        }

    def check(self, row=None, rate="35.125"):
        guard.validate_observation(
            currency="USD",
            company_currency="THB",
            rate=rate,
            observation=self.row if row is None else row,
            now=self.now,
        )

    def test_valid_direct_pair(self):
        self.check()

    def test_exact_freshness_boundary(self):
        self.row["as_of"] = "2026-09-07T12:00:00Z"
        self.check()
        self.row["as_of"] = "2026-09-07T11:59:59Z"
        with self.assertRaisesRegex(guard.FXRejected, "FX_SNAPSHOT_STALE"):
            self.check()

    def test_invalid_metadata(self):
        for field, value, code in [
            ("base_currency", "THB", "DIRECT_PAIR"),
            ("quality", "provisional", "UNVERIFIED"),
            ("source_type", "manual", "UNVERIFIED"),
            ("source_ref", " ", "PROVENANCE"),
            ("reviewed_by", None, "PROVENANCE"),
            ("as_of", "2026-09-09T11:00:00Z", "TIME_ALIGNMENT"),
            ("captured_at", "2026-09-08T10:00:00Z", "TIME_ALIGNMENT"),
            ("reviewed_at", "2026-09-08T10:00:00Z", "TIME_ALIGNMENT"),
            ("as_of", "2026-09-08T11:00:00", "TIME_ALIGNMENT"),
            ("rate", "35.126", "RATE_MISMATCH"),
        ]:
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(guard.FXRejected, code),
            ):
                self.check({**self.row, field: value})

    def test_invalid_numbers(self):
        for rate in ("NaN", "Infinity", "-1", "0", None, True, "n/a"):
            with (
                self.subTest(rate=rate),
                self.assertRaisesRegex(guard.FXRejected, "RATE_INVALID"),
            ):
                self.check(rate=rate)

    def test_missing_evidence(self):
        with self.assertRaisesRegex(guard.FXRejected, "SNAPSHOT_MISSING"):
            guard.validate_observation(
                currency="USD",
                company_currency="THB",
                rate=35,
                observation=None,
                now=self.now,
            )

    def test_base_currency(self):
        guard.validate_observation(
            currency="THB",
            company_currency="THB",
            rate=1,
            observation=None,
            now=self.now,
        )
        with self.assertRaisesRegex(guard.FXRejected, "RATE_MISMATCH"):
            guard.validate_observation(
                currency="THB",
                company_currency="THB",
                rate=35,
                observation=None,
                now=self.now,
            )

    def test_adapter_uses_trusted_snapshot_and_server_clock(self):
        now = datetime.now(UTC)
        row = {
            **self.row,
            **{
                key: (now - timedelta(minutes=2)).isoformat().replace("+00:00", "Z")
                for key in ("as_of", "captured_at", "reviewed_at")
            },
        }

        def throw(code):
            raise guard.FXRejected(code)

        fake = SimpleNamespace(
            db=SimpleNamespace(
                get_value=lambda *a: "THB", get_single_value=lambda *a: 1
            ),
            conf={"solo_fx_approved_snapshots": {"approved": row}},
            throw=throw,
        )
        doc = SimpleNamespace(
            company="fixture",
            currency="USD",
            conversion_rate="35.125",
            get=lambda field: "approved",
        )
        with patch.dict(sys.modules, frappe=fake):
            guard.validate_sales_invoice(doc)
            doc.get = lambda field: "forged"
            with self.assertRaisesRegex(guard.FXRejected, "SNAPSHOT_MISSING"):
                guard.validate_sales_invoice(doc)
            fake.db.get_single_value = lambda *a: 0
            with self.assertRaisesRegex(guard.FXRejected, "EXTERNAL_LOOKUP_ENABLED"):
                guard.validate_sales_invoice(doc)


if __name__ == "__main__":
    unittest.main()
