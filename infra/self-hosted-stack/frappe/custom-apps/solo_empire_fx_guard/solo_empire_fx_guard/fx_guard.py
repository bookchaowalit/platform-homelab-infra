"""Trusted, provider-free FX validation for Sales Invoice before_submit."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation


class FXRejected(ValueError):
    """Contains only a stable reason code, never document or source data."""


def timestamp(value):
    try:
        if not isinstance(value, str) or not value.endswith("Z"):
            raise ValueError
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except (TypeError, ValueError):
        raise FXRejected("FX_TIME_ALIGNMENT_INVALID") from None


def amount(value):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number <= 0:
            raise InvalidOperation
        return number
    except (InvalidOperation, ValueError, TypeError):
        raise FXRejected("FX_RATE_INVALID") from None


def validate_observation(*, currency, company_currency, rate, observation, now):
    """Validate one direct observation at server submission time (inclusive 24h)."""
    if not currency or not company_currency:
        raise FXRejected("FX_CURRENCY_MISSING")
    if currency == company_currency:
        if amount(rate) != 1:
            raise FXRejected("FX_RATE_MISMATCH")
        return
    if not isinstance(observation, dict):
        raise FXRejected("FX_SNAPSHOT_MISSING")
    if (observation.get("base_currency"), observation.get("quote_currency")) != (
        currency, company_currency
    ):
        raise FXRejected("FX_DIRECT_PAIR_REQUIRED")
    if observation.get("quality") != "verified" or observation.get("source_type") != "reference":
        raise FXRejected("FX_SNAPSHOT_UNVERIFIED")
    for field in ("source_ref", "reviewed_by"):
        if not isinstance(observation.get(field), str) or not observation[field].strip():
            raise FXRejected("FX_PROVENANCE_MISSING")
    observed = timestamp(observation.get("as_of"))
    captured = timestamp(observation.get("captured_at"))
    reviewed = timestamp(observation.get("reviewed_at"))
    if now.tzinfo is None or not observed <= captured <= reviewed <= now:
        raise FXRejected("FX_TIME_ALIGNMENT_INVALID")
    if now - observed > timedelta(hours=24):
        raise FXRejected("FX_SNAPSHOT_STALE")
    if amount(rate) != amount(observation.get("rate")):
        raise FXRejected("FX_RATE_MISMATCH")


def validate_sales_invoice(doc, method=None):
    """Frappe before_submit adapter: every non-base invoice requires evidence."""
    import frappe

    try:
        company_currency = frappe.db.get_value("Company", doc.company, "default_currency")
        observation = None
        if doc.currency != company_currency:
            if frappe.db.get_single_value("Currency Exchange Settings", "disabled") != 1:
                raise FXRejected("FX_EXTERNAL_LOOKUP_ENABLED")
            snapshots = frappe.conf.get("solo_fx_approved_snapshots")
            snapshot_id = doc.get("custom_fx_snapshot_id")
            if not isinstance(snapshot_id, str) or not snapshot_id.strip():
                raise FXRejected("FX_SNAPSHOT_MISSING")
            if not isinstance(snapshots, dict):
                raise FXRejected("FX_SNAPSHOT_MISSING")
            observation = snapshots.get(snapshot_id)
        validate_observation(
            currency=doc.currency,
            company_currency=company_currency,
            rate=doc.conversion_rate,
            observation=observation,
            now=datetime.now(timezone.utc),
        )
    except FXRejected as exc:
        frappe.throw(str(exc))
