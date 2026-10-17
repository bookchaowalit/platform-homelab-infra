from . import __version__ as app_version  # noqa: F401 - Frappe reads app_version from the hooks module

app_name = "solo_empire_fx_guard"
app_title = "Solo Empire FX Guard"
app_publisher = "Solo Empire"
app_description = "Fail-closed exchange-rate submission guard"
app_email = "internal@solo-empire.local"
app_license = "MIT"

after_install = "solo_empire_fx_guard.install.after_install"
before_uninstall = "solo_empire_fx_guard.install.before_uninstall"

doc_events = {
    "Sales Invoice": {
        "before_submit": "solo_empire_fx_guard.fx_guard.validate_sales_invoice",
    }
}
