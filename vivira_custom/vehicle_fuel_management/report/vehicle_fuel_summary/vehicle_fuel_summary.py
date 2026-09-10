import frappe
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	fuel_type_label = get_label("Fuel Issue", "fuel_type", "Fuel Type")
	columns = [
		{"label": "Vehicle No", "fieldname": "vehicle_no", "fieldtype": "Data", "width": 120},
		{"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 140},
		{"label": "Owner / Supplier", "fieldname": "owner_supplier", "fieldtype": "Data", "width": 170},
		{"label": fuel_type_label, "fieldname": "fuel_type", "fieldtype": "Link", "options": "Item", "width": 140},
		{"label": "Total Qty Issued", "fieldname": "total_qty_issued", "fieldtype": "Float", "width": 135},
		{"label": "First Odometer", "fieldname": "first_odometer", "fieldtype": "Float", "width": 125},
		{"label": "Last Odometer", "fieldname": "last_odometer", "fieldtype": "Float", "width": 125},
		{"label": "Distance", "fieldname": "distance", "fieldtype": "Float", "width": 110},
		{"label": "Average Mileage", "fieldname": "average_mileage", "fieldtype": "Float", "width": 130},
	]
	conditions, values = get_conditions(filters)
	data = frappe.db.sql(
		f"""
		select
			vehicle_no,
			vehicle,
			coalesce(nullif(owner_name, ''), supplier) as owner_supplier,
			fuel_type,
			sum(qty_issued) as total_qty_issued,
			min(nullif(previous_odometer_reading, 0)) as first_odometer,
			max(nullif(current_odometer_reading, 0)) as last_odometer,
			sum(distance_travelled) as distance,
			case
				when sum(case when distance_travelled > 0 then qty_issued else 0 end) > 0
				then sum(distance_travelled) / sum(case when distance_travelled > 0 then qty_issued else 0 end)
				else 0
			end as average_mileage
		from `tabFuel Issue`
		where docstatus = 1 {conditions}
		group by vehicle_no, vehicle, owner_supplier, fuel_type
		order by vehicle_no, vehicle, fuel_type
		""",
		values,
		as_dict=True,
	)
	for row in data:
		row.average_mileage = flt(row.average_mileage)
	return columns, data, None, None, [
		{"label": "Total Qty Issued", "value": sum(flt(row.total_qty_issued) for row in data), "indicator": "Orange"},
		{"label": "Total Distance", "value": sum(flt(row.distance) for row in data), "indicator": "Blue"},
	]


def get_label(doctype, fieldname, fallback):
	field = frappe.get_meta(doctype).get_field(fieldname)
	return field.label if field and field.label else fallback


def get_conditions(filters):
	conditions = []
	values = {}
	for field in ("company", "project", "fuel_type", "vehicle"):
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
