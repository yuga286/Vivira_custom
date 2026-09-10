import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class FuelLedgerEntry(Document):
	def validate(self):
		if flt(self.received_qty) < 0 or flt(self.issued_qty) < 0:
			frappe.throw(_("Fuel Ledger quantities cannot be negative."))
		if flt(self.received_qty) and flt(self.issued_qty):
			frappe.throw(_("Fuel Ledger Entry cannot have both received and issued quantity."))
		if not flt(self.received_qty) and not flt(self.issued_qty):
			frappe.throw(_("Fuel Ledger Entry must have received or issued quantity."))
