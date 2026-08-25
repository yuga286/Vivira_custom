import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_link_to_form


class RoomRentEntry(Document):
	def validate(self):
		self.validate_period()
		self.validate_room_rents()
		self.set_totals()

	def validate_period(self):
		if self.start_date and self.end_date and self.start_date > self.end_date:
			frappe.throw(_("End Date cannot be before Start Date."))

	def validate_room_rents(self):
		seen = set()
		for row in self.room_rents:
			if not row.room_rent:
				continue

			if row.room_rent in seen:
				frappe.throw(
					_("Room Rent {0} is repeated in row {1}.").format(
						frappe.bold(row.room_rent), row.idx
					)
				)
			seen.add(row.room_rent)

	def set_totals(self):
		self.number_of_room_rents = len([row for row in self.room_rents if row.room_rent])
		self.total_rent_amount = sum(flt(row.rent_amount) for row in self.room_rents)

	@frappe.whitelist()
	def get_room_rent(self):
		self.check_permission("write")
		self.validate_period()

		room_rents = get_active_room_rents()
		self.set("room_rents", [])

		for room_rent in room_rents:
			self.append(
				"room_rents",
				{
					"room_rent": room_rent.name,
					"supplier": room_rent.supplier,
					"no_of_rooms": room_rent.no_of_rooms,
					"no_of_workers": room_rent.no_of_workers,
					"rent_amount": room_rent.monthly_rent,
				},
			)

		self.set_totals()

		if not self.room_rents:
			frappe.throw(_("No active Room Rent records found."), title=_("No Room Rent Found"))

		return {
			"number_of_room_rents": self.number_of_room_rents,
			"total_rent_amount": self.total_rent_amount,
		}

	@frappe.whitelist()
	def create_room_rent_slips(self):
		self.check_permission("write")

		if self.docstatus != 1:
			frappe.throw(_("Submit the Room Rent Entry before creating Room Rent Slips."))

		if not self.room_rents:
			frappe.throw(_("Get Room Rent before creating Room Rent Slips."))

		created = []
		existing = []

		for row in self.room_rents:
			if not row.room_rent:
				continue

			slip_name = get_existing_room_rent_slip(self.name, row.room_rent)
			if slip_name:
				existing.append(slip_name)
			else:
				slip = make_room_rent_slip(self, row)
				slip.insert()
				slip_name = slip.name
				created.append(slip_name)

			if row.room_rent_slip != slip_name:
				row.db_set("room_rent_slip", slip_name, update_modified=False)

		self.db_set("room_rent_slips_created", 1, update_modified=False)
		self.reload()

		message = _("Created {0} Room Rent Slip(s).").format(len(created))
		if existing:
			message += "<br>" + _("Skipped {0} existing Room Rent Slip(s).").format(len(existing))

		if created:
			message += "<br>" + _("New slips: {0}").format(
				", ".join(get_link_to_form("Room Rent Slip", name) for name in created)
			)

		frappe.msgprint(message, indicator="green", title=_("Room Rent Slips"))
		return {"created": created, "existing": existing}


def get_active_room_rents():
	return frappe.get_all(
		"Room Rent",
		filters={"status": "Active", "docstatus": ["<", 2]},
		fields=[
			"name",
			"supplier",
			"date_of_entry",
			"no_of_rooms",
			"no_of_workers",
			"monthly_rent",
			"account_holder_name",
			"pan_no",
			"account_number",
			"ifsc_code",
			"bank_name",
		],
		order_by="name asc",
	)


def get_existing_room_rent_slip(room_rent_entry, room_rent):
	return frappe.db.get_value(
		"Room Rent Slip",
		{
			"room_rent_entry": room_rent_entry,
			"room_rent": room_rent,
			"docstatus": ["<", 2],
		},
		"name",
	)


def make_room_rent_slip(entry, row):
	room_rent = frappe.get_cached_doc("Room Rent", row.room_rent)
	total_amount = flt(row.rent_amount)

	slip = frappe.new_doc("Room Rent Slip")
	slip.room_rent_entry = entry.name
	slip.room_rent = row.room_rent
	slip.supplier = row.supplier or room_rent.supplier
	slip.posting_date = entry.posting_date
	slip.start_date = entry.start_date
	slip.end_date = entry.end_date
	slip.date_of_entry = room_rent.date_of_entry
	slip.no_of_rooms = row.no_of_rooms
	slip.no_of_workers = row.no_of_workers
	slip.account_holder_name = room_rent.account_holder_name
	slip.pan_no = room_rent.pan_no
	slip.account_number = room_rent.account_number
	slip.ifsc_code = room_rent.ifsc_code
	slip.bank_name = room_rent.bank_name
	slip.total_amount = total_amount
	slip.paid_amount = 0
	slip.outstanding_amount = total_amount
	slip.payment_status = "Unpaid"
	return slip
