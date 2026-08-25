from frappe import _


def get_data():
	return {
		"fieldname": "room_rent_entry",
		"transactions": [{"label": _("References"), "items": ["Room Rent Slip"]}],
	}
