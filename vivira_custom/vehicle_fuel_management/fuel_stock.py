import frappe
from frappe import _
from frappe.utils import flt, get_datetime


def get_posting_datetime(posting_date, posting_time=None):
	posting_time = posting_time or "00:00:00"
	return get_datetime(f"{posting_date} {posting_time}")


@frappe.whitelist()
def get_project_fuel_balance(project, fuel_type, posting_date=None, posting_time=None, exclude_voucher_no=None):
	if not project or not fuel_type:
		return 0

	values = {
		"project": project,
		"fuel_type": fuel_type,
		"posting_date": posting_date,
		"posting_time": posting_time,
		"exclude_voucher_no": exclude_voucher_no,
	}
	conditions = [
		"docstatus = 1",
		"project = %(project)s",
		"fuel_type = %(fuel_type)s",
	]

	if posting_date:
		conditions.append(
			"""(
				posting_date < %(posting_date)s
				or (posting_date = %(posting_date)s and coalesce(posting_time, '00:00:00') <= coalesce(%(posting_time)s, '00:00:00'))
			)"""
		)

	if exclude_voucher_no:
		conditions.append("voucher_no != %(exclude_voucher_no)s")

	result = frappe.db.sql(
		f"""
		select coalesce(sum(received_qty), 0) - coalesce(sum(issued_qty), 0)
		from `tabFuel Ledger Entry`
		where {" and ".join(conditions)}
		""",
		values,
	)[0][0]
	return flt(result)


def get_previous_balance(project, fuel_type, posting_date, posting_time=None, exclude_voucher_no=None):
	return get_project_fuel_balance(
		project,
		fuel_type,
		posting_date=posting_date,
		posting_time=posting_time,
		exclude_voucher_no=exclude_voucher_no,
	)


def get_opening_balance(project, fuel_type, posting_date):
	if not posting_date:
		return 0

	result = frappe.db.sql(
		"""
		select coalesce(sum(received_qty), 0) - coalesce(sum(issued_qty), 0)
		from `tabFuel Ledger Entry`
		where docstatus = 1 and project = %s and fuel_type = %s and posting_date < %s
		""",
		(project, fuel_type, posting_date),
	)[0][0]
	return flt(result)


def get_total_issued_today(project, fuel_type, posting_date, exclude_voucher_no=None, vehicle=None):
	if not (project and fuel_type and posting_date):
		return 0

	conditions = [
		"docstatus = 1",
		"project = %(project)s",
		"fuel_type = %(fuel_type)s",
		"posting_date = %(posting_date)s",
	]
	values = {
		"project": project,
		"fuel_type": fuel_type,
		"posting_date": posting_date,
		"exclude_voucher_no": exclude_voucher_no,
		"vehicle": vehicle,
	}
	if exclude_voucher_no:
		conditions.append("voucher_no != %(exclude_voucher_no)s")
	if vehicle:
		conditions.append("vehicle = %(vehicle)s")

	return flt(
		frappe.db.sql(
			f"""
			select coalesce(sum(issued_qty), 0)
			from `tabFuel Ledger Entry`
			where {" and ".join(conditions)}
			""",
			values,
		)[0][0]
	)


def get_previous_vehicle_issue(vehicle, posting_date=None, posting_time=None, exclude_voucher_no=None):
	if not vehicle:
		return None

	conditions = [
		"docstatus = 1",
		"vehicle = %(vehicle)s",
		"coalesce(current_odometer_reading, 0) > 0",
	]
	values = {
		"vehicle": vehicle,
		"posting_date": posting_date,
		"posting_time": posting_time,
		"exclude_voucher_no": exclude_voucher_no,
	}
	if posting_date:
		conditions.append(
			"""(
				posting_date < %(posting_date)s
				or (posting_date = %(posting_date)s and coalesce(posting_time, '00:00:00') <= coalesce(%(posting_time)s, '00:00:00'))
			)"""
		)
	if exclude_voucher_no:
		conditions.append("name != %(exclude_voucher_no)s")

	rows = frappe.db.sql(
		f"""
		select name, current_odometer_reading, qty_issued
		from `tabFuel Issue`
		where {" and ".join(conditions)}
		order by posting_date desc, posting_time desc, creation desc
		limit 1
		""",
		values,
		as_dict=True,
	)
	return rows[0] if rows else None


def get_item_uom(item):
	return frappe.db.get_value("Item", item, "stock_uom") if item else None


def make_fuel_ledger_entry(doc, received_qty=0, issued_qty=0):
	cancel_fuel_ledger_entries(doc.doctype, doc.name)
	ledger = frappe.get_doc(
		{
			"doctype": "Fuel Ledger Entry",
			"posting_date": doc.posting_date,
			"posting_time": doc.posting_time,
			"company": doc.company,
			"project": doc.project,
			"fuel_type": doc.fuel_type,
			"voucher_type": doc.doctype,
			"voucher_no": doc.name,
			"received_qty": received_qty,
			"issued_qty": issued_qty,
			"uom": doc.uom,
			"employee": doc.get("employee"),
			"vehicle": doc.get("vehicle"),
			"supplier": doc.get("supplier"),
			"remarks": doc.get("remarks"),
		}
	)
	ledger.flags.ignore_permissions = True
	ledger.insert()
	ledger.submit()


def cancel_fuel_ledger_entries(voucher_type, voucher_no):
	for name in frappe.get_all(
		"Fuel Ledger Entry",
		filters={"voucher_type": voucher_type, "voucher_no": voucher_no, "docstatus": 1},
		pluck="name",
	):
		ledger = frappe.get_doc("Fuel Ledger Entry", name)
		ledger.flags.ignore_permissions = True
		ledger.cancel()


def validate_project_fuel_balance(doc, requested_qty):
	available_qty = get_project_fuel_balance(
		doc.project,
		doc.fuel_type,
		posting_date=doc.posting_date,
		posting_time=doc.posting_time,
		exclude_voucher_no=doc.name if doc.name and not doc.is_new() else None,
	)
	if flt(requested_qty) > flt(available_qty):
		fuel_name = frappe.db.get_value("Item", doc.fuel_type, "item_name") or doc.fuel_type
		frappe.throw(
			_("Insufficient {0} Balance.<br>Project: {1}<br>Available: {2} {3}<br>Requested: {4} {3}").format(
				frappe.bold(fuel_name),
				frappe.bold(doc.project),
				flt(available_qty),
				doc.uom or "",
				flt(requested_qty),
			)
		)
