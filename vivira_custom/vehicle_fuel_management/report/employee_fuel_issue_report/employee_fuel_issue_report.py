import frappe


def execute(filters=None):
	filters = frappe._dict(filters or {})
	fuel_type_label = get_label("Fuel Issue", "fuel_type", "Fuel Type")
	columns = [
		{"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		{"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 160},
		{"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 130},
		{"label": fuel_type_label, "fieldname": "fuel_type", "fieldtype": "Link", "options": "Item", "width": 150},
		{"label": "Qty Issued", "fieldname": "qty_issued", "fieldtype": "Float", "width": 110},
		{"label": "Odometer", "fieldname": "current_odometer_reading", "fieldtype": "Float", "width": 120},
		{"label": "Mileage", "fieldname": "average_mileage", "fieldtype": "Float", "width": 100},
		{"label": "Fuel Issue Reference", "fieldname": "name", "fieldtype": "Link", "options": "Fuel Issue", "width": 155},
	]
	conditions, values = get_conditions(filters)
	data = frappe.db.sql(
		f"""
		select posting_date, employee, employee_name, project, vehicle, fuel_type,
			qty_issued, current_odometer_reading, average_mileage, name
		from `tabFuel Issue`
		where docstatus = 1 {conditions}
		order by posting_date asc, posting_time asc, creation asc
		""",
		values,
		as_dict=True,
	)
	return columns, data, None, None, [{"label": "Total Qty Issued", "value": sum(d.qty_issued for d in data), "indicator": "Blue"}]


def get_label(doctype, fieldname, fallback):
	field = frappe.get_meta(doctype).get_field(fieldname)
	return field.label if field and field.label else fallback


def get_conditions(filters):
	conditions = []
	values = {}
	for field in ("company", "project", "employee", "fuel_type", "vehicle"):
		if filters.get(field):
			conditions.append(f"and {field} = %({field})s")
			values[field] = filters[field]
	if filters.get("from_date"):
		conditions.append("and posting_date >= %(from_date)s")
		values["from_date"] = filters.from_date
	if filters.get("to_date"):
		conditions.append("and posting_date <= %(to_date)s")
		values["to_date"] = filters.to_date
	return " ".join(conditions), values
