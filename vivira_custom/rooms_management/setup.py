import frappe


def ensure_room_rent_slip_payment_entry_field():
	if frappe.db.exists("Custom Field", "Payment Entry-custom_room_rent_slip"):
		return

	custom_field = frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": "Payment Entry",
			"fieldname": "custom_room_rent_slip",
			"fieldtype": "Link",
			"label": "Room Rent Slip",
			"options": "Room Rent Slip",
			"insert_after": "party",
			"no_copy": 1,
		}
	)
	custom_field.insert(ignore_permissions=True)
	frappe.clear_cache(doctype="Payment Entry")
