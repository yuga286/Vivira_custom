import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowtime

from vivira_custom.vehicle_fuel_management.fuel_stock import (
	get_item_uom,
	get_previous_balance,
	make_fuel_ledger_entry,
)


class FuelReceipt(Document):
	def validate(self):
		self.set_defaults()
		self.validate_project_company()
		self.validate_qty_and_rate()
		self.set_amount_and_balances()

	def on_submit(self):
		make_fuel_ledger_entry(self, received_qty=self.qty)

	def on_cancel(self):
		from vivira_custom.vehicle_fuel_management.fuel_stock import cancel_fuel_ledger_entries

		current_balance = get_previous_balance(self.project, self.fuel_type, self.posting_date, self.posting_time)
		if flt(current_balance) - flt(self.qty) < 0:
			frappe.throw(_("Cannot cancel this Fuel Receipt because it would create negative fuel balance."))
		cancel_fuel_ledger_entries(self.doctype, self.name)

	def set_defaults(self):
		if not self.posting_time:
			self.posting_time = nowtime()
		if not self.company:
			self.company = frappe.defaults.get_user_default("Company")
		if self.fuel_type and not self.uom:
			self.uom = get_item_uom(self.fuel_type)
		if self.supplier and not self.supplier_name:
			self.supplier_name = frappe.db.get_value("Supplier", self.supplier, "supplier_name")

	def validate_qty_and_rate(self):
		if flt(self.qty) <= 0:
			frappe.throw(_("Quantity must be greater than zero."))
		if flt(self.unit_rate) < 0:
			frappe.throw(_("Unit Rate cannot be negative."))
		if not self.uom:
			frappe.throw(_("UOM is mandatory."))

	def validate_project_company(self):
		project_company = frappe.db.get_value("Project", self.project, "company")
		if project_company and self.company and project_company != self.company:
			frappe.throw(_("Project {0} belongs to Company {1}.").format(self.project, project_company))

	def set_amount_and_balances(self):
		self.total_amount = flt(self.qty) * flt(self.unit_rate)
		self.opening_balance = get_previous_balance(
			self.project,
			self.fuel_type,
			self.posting_date,
			self.posting_time,
			exclude_voucher_no=self.name if self.name and not self.is_new() else None,
		)
		self.closing_balance = flt(self.opening_balance) + flt(self.qty)
