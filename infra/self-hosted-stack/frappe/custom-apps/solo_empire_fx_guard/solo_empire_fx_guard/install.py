import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS = {
    "Sales Invoice": [
        {
            "fieldname": "custom_fx_snapshot_id",
            "fieldtype": "Data",
            "label": "FX Snapshot ID",
            "insert_after": "conversion_rate",
            "read_only": 1,
            "no_copy": 1,
            "description": "Server-selected approved FX observation identity.",
        }
    ]
}


def after_install():
    create_custom_fields(CUSTOM_FIELDS, update=True)


def before_uninstall():
    for field in CUSTOM_FIELDS["Sales Invoice"]:
        name = f"Sales Invoice-{field['fieldname']}"
        if frappe.db.exists("Custom Field", name):
            frappe.delete_doc("Custom Field", name, force=True)
