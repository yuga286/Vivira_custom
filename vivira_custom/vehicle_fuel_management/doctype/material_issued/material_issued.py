import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowtime

from vivira_custom.vehicle_fuel_management.fuel_stock import get_item_uom


class MaterialIssued(Document):
	def validate(self):
		self.set_defaults()
		self.set_employee_details()
		self.validate_project_company()
		self.validate_qty()

	def on_submit(self):
		self.sync_employee_history()

	def on_cancel(self):
		self.remove_employee_history()

	def set_defaults(self):
		if not self.posting_time:
			self.posting_time = nowtime()
		if not self.company:
			self.company = frappe.defaults.get_user_default("Company")
		if self.item:
			if not self.uom:
				self.uom = get_item_uom(self.item)
			if not self.item_name:
				self.item_name = frappe.db.get_value("Item", self.item, "item_name")

	def set_employee_details(self):
		if not self.employee:
			return

		employee = frappe.db.get_value(
			"Employee",
			self.employee,
			["employee_name", "subcontractor_supplier"],
			as_dict=True,
		)
		if not employee:
			return

		self.employee_name = employee.employee_name
		self.subcontractor_supplier = employee.subcontractor_supplier
		self.set_supplier_name()

	def set_supplier_name(self):
		if self.subcontractor_supplier:
			self.subcontractor_supplier_name = frappe.db.get_value(
				"Supplier", self.subcontractor_supplier, "supplier_name"
			)
		else:
			self.subcontractor_supplier_name = None

	def validate_project_company(self):
		project_company = frappe.db.get_value("Project", self.project, "company")
		if project_company and self.company and project_company != self.company:
			frappe.throw(_("Project {0} belongs to Company {1}.").format(self.project, project_company))

	def validate_qty(self):
		if flt(self.qty) <= 0:
			frappe.throw(_("Qty must be greater than zero."))
		if not self.uom:
			frappe.throw(_("UOM is mandatory."))

	def sync_employee_history(self):
		if not self.employee:
			return

		employee = frappe.get_doc("Employee", self.employee)
		history_field = get_employee_issue_history_field(employee)
		existing = None
		for row in employee.get(history_field) or []:
			if row.get("material_issued") == self.name:
				existing = row
				break

		row = existing or employee.append(history_field, {})
		row.update(
			{
				"posting_date": self.posting_date,
				"project": self.project,
				"subcontractor_supplier": self.subcontractor_supplier,
				"material_issued": self.name,
				"item": self.item,
				"item_name": self.item_name or frappe.db.get_value("Item", self.item, "item_name"),
				"qty": self.qty,
				"uom": self.uom,
			}
		)
		employee.flags.ignore_permissions = True
		employee.save()

	def remove_employee_history(self):
		if not self.employee:
			return

		employee = frappe.get_doc("Employee", self.employee)
		history_field = get_employee_issue_history_field(employee)
		rows = [
			row
			for row in employee.get(history_field) or []
			if row.get("material_issued") != self.name
		]
		employee.set(history_field, rows)
		employee.flags.ignore_permissions = True
		employee.save()


def get_employee_issue_history_field(employee):
	if employee.meta.has_field("issue_history"):
		return "issue_history"
	return "fuel_issue_history"
