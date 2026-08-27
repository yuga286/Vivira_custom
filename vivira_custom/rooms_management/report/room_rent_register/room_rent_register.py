import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data, None, None, get_summary(data)


def get_columns():

	return [
		{
			"label": _("CONTRACTOR"),
			"fieldname": "contractor",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("DATE OF ENTRY"),
			"fieldname": "date_of_entry",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"label": _("ADVANCE"),
			"fieldname": "advance_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("NO OF ROOMS"),
			"fieldname": "no_of_rooms",
			"fieldtype": "Int",
			"width": 110
		},
		{
			"label": _("MONTHLY RENT"),
			"fieldname": "monthly_rent",
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"label": _("NO OF WORKERS"),
			"fieldname": "no_of_workers",
			"fieldtype": "Int",
			"width": 120
		},
		{
			"label": _("LAST PAID DATE"),
			"fieldname": "last_paid_date",
			"fieldtype": "Date",
			"width": 130
		},
		{
			"label": _("ACCOUNT HOLDER NAME"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 180
		},
		{
			"label": _("PAN NO"),
			"fieldname": "pan_no",
			"fieldtype": "Data",
			"width": 130
		},
		{
			"label": _("ACCOUNT NUMBER"),
			"fieldname": "account_number",
			"fieldtype": "Data",
			"width": 160
		},
		{
			"label": _("IFSC CODE"),
			"fieldname": "ifsc_code",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("BANK NAME"),
			"fieldname": "bank_name",
			"fieldtype": "Data",
			"width": 160
		},
		{
			"label": _("Remarks"),
			"fieldname": "remarks",
			"fieldtype": "Data",
			"width": 160
		},
	]


def get_data(filters):
	conditions, values = get_conditions(filters)
	return frappe.db.sql(
		f"""
		select
			name,
			supplier,
			date_of_entry,
			no_of_rooms,
			no_of_workers,
			monthly_rent,
			advance_amount,
			account_holder_name,
			pan_no,
			account_number,
			ifsc_code,
			bank_name,
			paid_amount,
			outstanding_amount,
			status,
			last_paid_date,
			remarks
		from `tabRoom Rent`
		where {conditions}
		order by date_of_entry desc, modified desc
		""",
		values,
		as_dict=True,
	)


def get_conditions(filters):
	conditions = ["docstatus < 2"]
	values = {}
	if filters.get("status"):
		conditions.append("status = %(status)s")
		values["status"] = filters.status
	if filters.get("from_date"):
		conditions.append("date_of_entry >= %(from_date)s")
		values["from_date"] = filters.from_date
	if filters.get("to_date"):
		conditions.append("date_of_entry <= %(to_date)s")
		values["to_date"] = filters.to_date
	return " and ".join(conditions), values


def get_summary(data):
	return [
		{"label": _("Total Rooms"), "value": sum(flt(row.no_of_rooms) for row in data), "datatype": "Data"},
		{"label": _("Total Rent"), "value": sum(flt(row.monthly_rent) for row in data), "datatype": "Currency"},
		{"label": _("Total Works"), "value": sum(flt(row.no_of_workers) for row in data), "datatype": "Data"},
	]
