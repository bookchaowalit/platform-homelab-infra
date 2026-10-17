"""Host-test import for the versioned Solo Empire Frappe app guard."""

from pathlib import Path
import sys


_APP_ROOT = (
    Path(__file__).resolve().parents[2] / "self-hosted-stack" / "frappe" / "custom-apps"
)
sys.path.insert(0, str(_APP_ROOT))

from solo_empire_fx_guard.solo_empire_fx_guard.fx_guard import (  # noqa: E402
    FXRejected,
    amount,
    timestamp,
    validate_observation,
    validate_sales_invoice,
)

__all__ = [
    "FXRejected",
    "amount",
    "timestamp",
    "validate_observation",
    "validate_sales_invoice",
]
