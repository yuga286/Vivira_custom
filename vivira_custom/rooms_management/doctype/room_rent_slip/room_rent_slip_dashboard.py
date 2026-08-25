from frappe import _


def get_data():
	return {
		"fieldname": "room_rent_slip",
		"non_standard_fieldnames": {"Payment Entry": "custom_room_rent_slip"},
		"transactions": [{"label": _("References"), "items": ["Payment Entry"]}],
	}
