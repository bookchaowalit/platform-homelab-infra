#!/usr/bin/env python3
"""Offline tests for the Frappe dashboard-reader setup boundary."""

from __future__ import annotations

import os
import stat
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "infra" / "scripts" / "sync"))

from frappe_dashboard_reader import read_key_value_file, write_token_file  # noqa: E402


def test_token_file_is_minimal_and_private() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "dashboard-reader.env"
        write_token_file(
            path, "solo-empire.localhost", ("synthetic-key", "synthetic-secret")
        )
        values = read_key_value_file(path)
        assert values == {
            "site_name": "solo-empire.localhost",
            "api_key": "synthetic-key",
            "api_secret": "synthetic-secret",
        }
        assert stat.S_IMODE(os.stat(path).st_mode) == 0o600


def test_token_file_parser_ignores_unrelated_values() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "credentials.txt"
        path.write_text(
            "site_name=solo-empire.localhost\n"
            "admin_user=Administrator\n"
            "admin_password=synthetic-password\n"
            "ignored=not-read\n",
            encoding="utf-8",
        )
        values = read_key_value_file(path)
        assert values["site_name"] == "solo-empire.localhost"
        assert values["admin_user"] == "Administrator"
        assert "ignored" not in values


if __name__ == "__main__":
    test_token_file_is_minimal_and_private()
    test_token_file_parser_ignores_unrelated_values()
    print("✅ Frappe dashboard-reader tests passed")
