def update_room_rent_slip_from_payment_entry(doc, method=None):
	room_rent_slip = getattr(doc, "custom_room_rent_slip", None)
	if not room_rent_slip:
		return

	from vivira_custom.rooms_management.doctype.room_rent_slip.room_rent_slip import (
		update_room_rent_slip_payment_status,
	)

	update_room_rent_slip_payment_status(room_rent_slip)
