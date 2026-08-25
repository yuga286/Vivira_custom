import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class RoomRentSlip(Document):
	def validate(self):
		self.validate_period()
		self.set_missing_room_rent_values()
		self.update_payment_status(save=False)

	def on_submit(self):
		self.update_payment_status(save=True)

	def validate_period(self):
		if self.start_date and self.end_date and self.start_date > self.end_date:
			frappe.throw(_("End Date cannot be before Start Date."))

	def set_missing_room_rent_values(self):
		if not self.room_rent:
			return

		room_rent = frappe.get_cached_doc("Room Rent", self.room_rent)
		self.supplier = self.supplier or room_rent.supplier
		self.date_of_entry = self.date_of_entry or room_rent.date_of_entry
		self.no_of_rooms = self.no_of_rooms or room_rent.no_of_rooms
		self.no_of_workers = self.no_of_workers or room_rent.no_of_workers
		self.account_holder_name = self.account_holder_name or room_rent.account_holder_name
		self.pan_no = self.pan_no or room_rent.pan_no
		self.account_number = self.account_number or room_rent.account_number
		self.ifsc_code = self.ifsc_code or room_rent.ifsc_code
		self.bank_name = self.bank_name or room_rent.bank_name

		if not self.total_amount:
			self.total_amount = room_rent.monthly_rent

	def update_payment_status(self, save=True):
		paid_amount = get_paid_amount(self.name) if self.name else 0
		outstanding_amount = max(flt(self.total_amount) - flt(paid_amount), 0)

		if flt(paid_amount) <= 0:
			payment_status = "Unpaid"
		elif flt(paid_amount) < flt(self.total_amount):
			payment_status = "Partially Paid"
		else:
			payment_status = "Paid"

		values = {
			"paid_amount": paid_amount,
			"outstanding_amount": outstanding_amount,
			"payment_status": payment_status,
		}

		if save and not self.is_new():
			self.db_set(values, update_modified=False)
			self.reload()
		else:
			self.update(values)


def get_paid_amount(room_rent_slip):
	if not room_rent_slip or not frappe.db.has_column("Payment Entry", "custom_room_rent_slip"):
		return 0

	result = frappe.db.sql(
		"""
		select sum(coalesce(paid_amount, received_amount, 0))
		from `tabPayment Entry`
		where docstatus = 1
			and payment_type = 'Pay'
			and custom_room_rent_slip = %s
		""",
		room_rent_slip,
	)
	return flt(result[0][0]) if result else 0


def update_room_rent_slip_payment_status(room_rent_slip):
	if not room_rent_slip:
		return

	if frappe.db.exists("Room Rent Slip", room_rent_slip):
		slip = frappe.get_doc("Room Rent Slip", room_rent_slip)
		slip.update_payment_status(save=True)
