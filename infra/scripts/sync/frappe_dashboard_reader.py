#!/usr/bin/env python3
"""Provision a bounded read-only Frappe user for the Solo Empire dashboard.

The command is dry-run by default. ``--apply`` is the explicit local mutation
that creates one custom role, grants read permission only on the dashboard
DocTypes, creates/updates one named System User, generates an API token, and
writes that token only to the ignored Frappe runtime directory.

No credential value is printed. The token file is intentionally outside Git.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import stat
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRAPPE_DIR = ROOT / "infra" / "self-hosted-stack" / "frappe"
DEFAULT_ADMIN_CREDENTIALS = FRAPPE_DIR / ".runtime" / "credentials.txt"
DEFAULT_TOKEN_FILE = FRAPPE_DIR / ".runtime" / "dashboard-reader.env"
DEFAULT_BASE_URL = "http://127.0.0.1:8090"
DEFAULT_SITE = "solo-empire.localhost"
DEFAULT_CONTAINER = "solo-empire-frappe-backend-1"
READER_ROLE = "Solo Empire Dashboard Reader"
READER_USER = "solo-empire-dashboard@solo-empire.local"
DASHBOARD_DOCTYPES = (
    "CRM Lead",
    "CRM Deal",
    "Customer",
    "Sales Invoice",
    "Project",
    "ToDo",
)


class FrappeRequestError(RuntimeError):
    def __init__(self, code: str, status: int | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.status = status


def read_key_value_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for line in lines:
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        key, separator, value = raw.partition("=")
        if not separator:
            key, separator, value = raw.partition(":")
        if separator and key.strip() in {
            "site_name",
            "admin_user",
            "admin_password",
            "api_key",
            "api_secret",
        }:
            values[key.strip()] = value.strip()
    return values


def safe_http_error(exc: urllib.error.HTTPError) -> FrappeRequestError:
    if exc.code in {401, 403}:
        return FrappeRequestError("authentication_or_permission_failed", exc.code)
    if exc.code == 404:
        return FrappeRequestError("not_found", exc.code)
    return FrappeRequestError(f"http_{exc.code}", exc.code)


class FrappeAdminClient:
    def __init__(self, base_url: str, site: str, user: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.site = site
        self.user = user
        self.password = password
        self.cookies = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies)
        )

    def login(self) -> None:
        self.request(
            "POST",
            "/api/method/login",
            payload={"usr": self.user, "pwd": self.password},
            form=True,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
        token: tuple[str, str] | None = None,
        form: bool = False,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        headers = {
            "Accept": "application/json",
            "Host": self.site,
        }
        data: bytes | None = None
        if payload is not None:
            if form:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                data = urllib.parse.urlencode(payload).encode("utf-8")
            else:
                headers["Content-Type"] = "application/json"
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if token:
            headers["Authorization"] = f"token {token[0]}:{token[1]}"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=10) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise safe_http_error(exc) from None
        except (urllib.error.URLError, TimeoutError):
            raise FrappeRequestError("unreachable") from None
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            raise FrappeRequestError("invalid_response") from None
        if not isinstance(body, dict):
            raise FrappeRequestError("invalid_response")
        return body

    def get(self, doctype: str, name: str) -> dict[str, Any] | None:
        try:
            body = self.request(
                "GET",
                f"/api/resource/{urllib.parse.quote(doctype, safe='')}/{urllib.parse.quote(name, safe='')}",
            )
        except FrappeRequestError as exc:
            if exc.status == 404:
                return None
            raise
        data = body.get("data")
        return data if isinstance(data, dict) else None

    def list(
        self,
        doctype: str,
        *,
        fields: list[str],
        filters: list[list[str]] | None = None,
        token: tuple[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        query = {
            "fields": json.dumps(fields),
            "limit_page_length": "100",
        }
        if filters:
            query["filters"] = json.dumps(filters)
        body = self.request(
            "GET",
            f"/api/resource/{urllib.parse.quote(doctype, safe='')}",
            query=query,
            token=token,
        )
        data = body.get("data")
        return data if isinstance(data, list) else []

    def create(self, doctype: str, values: dict[str, Any]) -> dict[str, Any]:
        body = self.request(
            "POST",
            f"/api/resource/{urllib.parse.quote(doctype, safe='')}",
            payload={"doctype": doctype, **values},
        )
        data = body.get("data")
        return data if isinstance(data, dict) else {}

    def update(self, doctype: str, name: str, values: dict[str, Any]) -> dict[str, Any]:
        body = self.request(
            "PUT",
            f"/api/resource/{urllib.parse.quote(doctype, safe='')}/{urllib.parse.quote(name, safe='')}",
            payload=values,
        )
        data = body.get("data")
        return data if isinstance(data, dict) else {}

    def generate_keys(self, user: str) -> tuple[str, str]:
        body = self.request(
            "POST",
            "/api/method/frappe.core.doctype.user.user.generate_keys",
            payload={"user": user},
            form=True,
        )
        message = body.get("message")
        if (
            not isinstance(message, dict)
            or not message.get("api_key")
            or not message.get("api_secret")
        ):
            raise FrappeRequestError("invalid_token_response")
        return str(message["api_key"]), str(message["api_secret"])


def add_read_permission(container: str, site: str, doctype: str) -> None:
    kwargs = json.dumps(
        {"doctype": doctype, "role": READER_ROLE, "permlevel": 0, "ptype": "read"},
        separators=(",", ":"),
    )
    command = [
        "docker",
        "exec",
        container,
        "bench",
        "--site",
        site,
        "execute",
        "frappe.permissions.add_permission",
        "--kwargs",
        kwargs,
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=60, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"permission_setup_failed:{doctype}")


def write_token_file(path: Path, site: str, token: tuple[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"site_name={site}\napi_key={token[0]}\napi_secret={token[1]}\n",
        encoding="utf-8",
    )
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def load_admin_values(path: Path, site: str) -> tuple[str, str, str]:
    values = read_key_value_file(path)
    user = values.get("admin_user", "")
    password = values.get("admin_password", "")
    if not user or not password:
        raise RuntimeError("admin_credentials_missing")
    return values.get("site_name", site), user, password


def verify_token(client: FrappeAdminClient, token: tuple[str, str]) -> dict[str, Any]:
    read_results: dict[str, bool] = {}
    counts: dict[str, int] = {}
    for doctype in DASHBOARD_DOCTYPES:
        rows = client.list(doctype, fields=["name"], token=token)
        read_results[doctype] = True
        counts[doctype] = len(rows)

    custom_perms = client.list(
        "Custom DocPerm",
        fields=[
            "parent",
            "role",
            "read",
            "write",
            "create",
            "delete",
            "submit",
            "cancel",
            "amend",
            "share",
        ],
        filters=[["role", "=", READER_ROLE]],
    )
    expected_doctypes = set(DASHBOARD_DOCTYPES)
    relevant_perms = [
        row for row in custom_perms if row.get("parent") in expected_doctypes
    ]
    permission_by_doctype = {str(row.get("parent")): row for row in relevant_perms}
    write_none = len(permission_by_doctype) == len(expected_doctypes) and all(
        not any(
            bool(row.get(field))
            for field in (
                "write",
                "create",
                "delete",
                "submit",
                "cancel",
                "amend",
                "share",
            )
        )
        for row in permission_by_doctype.values()
    )
    return {
        "read_all": all(read_results.values()),
        "write_none": write_none,
        "read": read_results,
        "counts": counts,
    }


def inspect_state(client: FrappeAdminClient, token_file: Path) -> dict[str, Any]:
    role = client.get("Role", READER_ROLE)
    user = client.get("User", READER_USER)
    token_values = read_key_value_file(token_file)
    custom_perms = client.list(
        "Custom DocPerm",
        fields=[
            "parent",
            "role",
            "read",
            "write",
            "create",
            "delete",
            "report",
            "export",
        ],
        filters=[["role", "=", READER_ROLE]],
    )
    return {
        "role_exists": role is not None,
        "user_exists": user is not None,
        "token_file_exists": bool(
            token_values.get("api_key") and token_values.get("api_secret")
        ),
        "custom_permission_rows": len(custom_perms),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    site, admin_user, admin_password = load_admin_values(
        Path(args.credentials), args.site
    )
    client = FrappeAdminClient(args.base_url, site, admin_user, admin_password)
    client.login()
    before = inspect_state(client, Path(args.token_file))
    result: dict[str, Any] = {
        "mode": "apply" if args.apply else "dry-run",
        "status": "planned" if not args.apply else "applied",
        "site": site,
        "base_url": args.base_url,
        "role": READER_ROLE,
        "user": READER_USER,
        "doctypes": list(DASHBOARD_DOCTYPES),
        "token_file": str(Path(args.token_file)),
        "before": before,
        "read_only": True,
        "write_performed": False,
    }
    if not args.apply:
        return result

    role = client.get("Role", READER_ROLE)
    if role is None:
        client.create(
            "Role",
            {"role_name": READER_ROLE, "is_custom": 1, "desk_access": 1, "disabled": 0},
        )
    else:
        # Frappe derives System User vs Website User from desk access. The
        # reader still has no write permissions, but must be a System User so
        # token-authenticated REST reads are evaluated against its role.
        client.update("Role", READER_ROLE, {"desk_access": 1, "disabled": 0})
    for doctype in DASHBOARD_DOCTYPES:
        add_read_permission(args.container, site, doctype)

    user_values = {
        "enabled": 1,
        "user_type": "System User",
        "first_name": "Solo Empire",
        "last_name": "Dashboard Reader",
        "send_welcome_email": 0,
        "roles": [{"doctype": "Has Role", "role": READER_ROLE}],
    }
    user = client.get("User", READER_USER)
    if user is None:
        client.create(
            "User",
            {
                "email": READER_USER,
                "new_password": secrets.token_urlsafe(24),
                **user_values,
            },
        )
    else:
        client.update("User", READER_USER, user_values)

    token_values = read_key_value_file(Path(args.token_file))
    token = (token_values.get("api_key", ""), token_values.get("api_secret", ""))
    token_verification: dict[str, Any] | None = None
    if token[0] and token[1]:
        try:
            token_verification = verify_token(client, token)
        except FrappeRequestError:
            token_verification = None
    if (
        not token_verification
        or not token_verification["read_all"]
        or not token_verification["write_none"]
    ):
        # Frappe's generate_keys implementation only persists a new secret
        # when the user has no API key. Clear this reader's old key first so
        # the returned pair is the pair stored in Frappe.
        client.update("User", READER_USER, {"api_key": ""})
        token = client.generate_keys(READER_USER)
        write_token_file(Path(args.token_file), site, token)
        token_verification = verify_token(client, token)

    if not token_verification["read_all"] or not token_verification["write_none"]:
        raise RuntimeError("reader_permission_verification_failed")
    result["write_performed"] = True
    result["after"] = inspect_state(client, Path(args.token_file))
    result["token_ready"] = True
    result["token_verification"] = {
        "read_all": token_verification["read_all"],
        "write_none": token_verification["write_none"],
        "counts": token_verification["counts"],
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="perform the local Frappe setup"
    )
    parser.add_argument(
        "--json", action="store_true", help="emit a machine-readable safe report"
    )
    parser.add_argument(
        "--base-url", default=os.environ.get("FRAPPE_BASE_URL", DEFAULT_BASE_URL)
    )
    parser.add_argument(
        "--site", default=os.environ.get("FRAPPE_SITE_NAME", DEFAULT_SITE)
    )
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--credentials", default=str(DEFAULT_ADMIN_CREDENTIALS))
    parser.add_argument("--token-file", default=str(DEFAULT_TOKEN_FILE))
    args = parser.parse_args(argv)
    try:
        report = run(args)
    except (
        FrappeRequestError,
        OSError,
        RuntimeError,
        subprocess.SubprocessError,
    ) as exc:
        report = {
            "mode": "apply" if args.apply else "dry-run",
            "status": "blocked",
            "error_code": str(exc),
            "write_performed": False,
            "read_only": True,
        }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Frappe dashboard reader: {report['status']}")
        if report.get("error_code"):
            print(f"  error: {report['error_code']}")
        else:
            print(
                f"  mode: {report['mode']}; role: {report['role']}; user: {report['user']}"
            )
            print(
                f"  write performed: {report['write_performed']}; token ready: {report.get('token_ready', False)}"
            )
    return 0 if report["status"] in {"planned", "applied"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
