import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowtime

from vivira_custom.vehicle_fuel_management.fuel_stock import (
	get_item_uom,
	get_previous_vehicle_issue,
	get_project_fuel_balance,
	get_total_issued_today,
	make_fuel_ledger_entry,
	validate_project_fuel_balance,
)


class FuelIssue(Document):
	def validate(self):
		self.set_defaults()
		self.set_vehicle_details()
		self.set_employee_details()
		self.validate_project_company()
		self.validate_qty()
		self.set_stock_and_mileage_values()
		if self.docstatus == 1 or self.get("_action") == "submit":
			validate_project_fuel_balance(self, self.qty_issued)

	def on_submit(self):
		self.set_stock_and_mileage_values()
		validate_project_fuel_balance(self, self.qty_issued)
		make_fuel_ledger_entry(self, issued_qty=self.qty_issued)
		self.update_vehicle_odometer()

	def on_cancel(self):
		from vivira_custom.vehicle_fuel_management.fuel_stock import cancel_fuel_ledger_entries

		cancel_fuel_ledger_entries(self.doctype, self.name)

	def set_defaults(self):
		if not self.posting_time:
			self.posting_time = nowtime()
		if not self.company:
			self.company = frappe.defaults.get_user_default("Company")
		if self.fuel_type and not self.uom:
			self.uom = get_item_uom(self.fuel_type)

	def set_vehicle_details(self):
		if not self.vehicle:
			return

		vehicle = frappe.db.get_value(
			"Vehicle",
			self.vehicle,
			[
				"license_plate",
				"make",
				"model",
				"employee",
				"fuel_type",
				"uom",
				"ownership_status",
				"vehicle_supplier",
				"owner_name",
				"current_project",
			],
			as_dict=True,
		)
		if not vehicle:
			return

		self.vehicle_no = vehicle.license_plate or self.vehicle
		self.vehicle_name = " ".join(filter(None, [vehicle.make, vehicle.model]))
		if not self.employee and vehicle.employee:
			self.employee = vehicle.employee
		if not self.fuel_type and vehicle.fuel_type and frappe.db.exists("Item", vehicle.fuel_type):
			self.fuel_type = vehicle.fuel_type
		if not self.uom and vehicle.uom:
			self.uom = vehicle.uom
		if not self.project and vehicle.current_project:
			self.project = vehicle.current_project
		if not self.vehicle_status and vehicle.ownership_status:
			self.vehicle_status = vehicle.ownership_status
		if not self.supplier and vehicle.vehicle_supplier:
			self.supplier = vehicle.vehicle_supplier
		if not self.owner_name and vehicle.owner_name:
			self.owner_name = vehicle.owner_name

	def set_employee_details(self):
		if self.employee:
			self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
		if self.supplier and self.owner_type == "Supplier":
			self.owner_name = frappe.db.get_value("Supplier", self.supplier, "supplier_name")
		if not self.owner_type:
			self.owner_type = "Company" if self.vehicle_status == "Own" else "Other"

	def validate_qty(self):
		if flt(self.qty_issued) <= 0:
			frappe.throw(_("Quantity Issued must be greater than zero."))
		if not self.vehicle:
			frappe.throw(_("Vehicle is mandatory for Fuel Issue."))
		if not self.uom:
			frappe.throw(_("UOM is mandatory."))

	def validate_project_company(self):
		project_company = frappe.db.get_value("Project", self.project, "company")
		if project_company and self.company and project_company != self.company:
			frappe.throw(_("Project {0} belongs to Company {1}.").format(self.project, project_company))

	def set_stock_and_mileage_values(self):
		exclude = self.name if self.name and not self.is_new() else None
		self.available_qty = get_project_fuel_balance(
			self.project,
			self.fuel_type,
			posting_date=self.posting_date,
			posting_time=self.posting_time,
			exclude_voucher_no=exclude,
		)
		self.total_issued_today = get_total_issued_today(
			self.project, self.fuel_type, self.posting_date, exclude_voucher_no=exclude
		) + flt(self.qty_issued)
		self.total_vehicle_issued_today = get_total_issued_today(
			self.project,
			self.fuel_type,
			self.posting_date,
			exclude_voucher_no=exclude,
			vehicle=self.vehicle,
		) + flt(self.qty_issued)

		previous_issue = get_previous_vehicle_issue(
			self.vehicle, self.posting_date, self.posting_time, exclude_voucher_no=exclude
		)
		if previous_issue:
			self.previous_odometer_reading = flt(previous_issue.current_odometer_reading)
			self.previous_fuel_qty = flt(previous_issue.qty_issued)
		else:
			self.previous_odometer_reading = 0
			self.previous_fuel_qty = 0

		self.distance_travelled = 0
		self.average_mileage = 0
		if flt(self.current_odometer_reading) and flt(self.previous_odometer_reading):
			if flt(self.current_odometer_reading) < flt(self.previous_odometer_reading):
				frappe.throw(_("Current Odometer Reading cannot be less than Previous Odometer Reading."))
			self.distance_travelled = flt(self.current_odometer_reading) - flt(self.previous_odometer_reading)
			if flt(self.qty_issued) > 0 and flt(self.distance_travelled) > 0:
				self.average_mileage = flt(self.distance_travelled) / flt(self.qty_issued)

		self.valuation_rate = self.get_weighted_average_rate()
		self.issue_amount = flt(self.qty_issued) * flt(self.valuation_rate)

	def get_weighted_average_rate(self):
		row = frappe.db.sql(
			"""
			select
				coalesce(sum(total_amount), 0) as amount,
				coalesce(sum(qty), 0) as qty
			from `tabFuel Receipt`
			where docstatus = 1 and project = %s and fuel_type = %s
			""",
			(self.project, self.fuel_type),
			as_dict=True,
		)[0]
		return flt(row.amount) / flt(row.qty) if flt(row.qty) else 0

	def update_vehicle_odometer(self):
		if self.vehicle and flt(self.current_odometer_reading):
			current = flt(frappe.db.get_value("Vehicle", self.vehicle, "last_odometer"))
			if flt(self.current_odometer_reading) > current:
				frappe.db.set_value(
					"Vehicle", self.vehicle, "last_odometer", flt(self.current_odometer_reading)
				)
