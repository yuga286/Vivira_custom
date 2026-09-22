import frappe
from frappe.utils import flt


DIMENSION_FIELDS = (
	"thickness_mm",
	"width_mm",
	"length_mm",
	"unit_weight_kg_sqm",
)


def calculate_bom_dimensions(doc, method=None):
	for row in doc.get("items", []):
		calculate_row_dimensions(row, "qty")


def calculate_work_order_dimensions(doc, method=None):
	copy_bom_dimensions_to_work_order(doc)
	for row in doc.get("required_items", []):
		calculate_row_dimensions(row, "required_qty")


def calculate_row_dimensions(row, qty_field):
	total_area = (flt(row.get("width_mm")) * flt(row.get("length_mm")) * flt(row.get(qty_field))) / 1000000
	row.total_area_sqm = flt(total_area, 6)
	row.total_weight_kg = flt(row.total_area_sqm * flt(row.get("unit_weight_kg_sqm")), 6)


def copy_bom_dimensions_to_work_order(doc):
	if not doc.get("bom_no") or not doc.get("required_items"):
		return

	bom_rows = get_bom_dimension_rows(doc.bom_no)
	if not bom_rows:
		return

	for row in doc.get("required_items", []):
		source = find_bom_dimension_row(row, bom_rows)
		if not source:
			continue
		for fieldname in DIMENSION_FIELDS:
			row.set(fieldname, source.get(fieldname))


def get_bom_dimension_rows(bom_no):
	rows = frappe.get_all(
		"BOM Item",
		filters={"parent": bom_no},
		fields=["item_code", "operation", *DIMENSION_FIELDS],
		order_by="idx asc",
	)
	by_item_operation = {}
	by_item = {}
	for row in rows:
		if row.operation:
			by_item_operation.setdefault((row.item_code, row.operation), row)
		by_item.setdefault(row.item_code, row)

	return {"by_item_operation": by_item_operation, "by_item": by_item}


def find_bom_dimension_row(work_order_item, bom_rows):
	if work_order_item.get("operation"):
		source = bom_rows["by_item_operation"].get(
			(work_order_item.get("item_code"), work_order_item.get("operation"))
		)
		if source:
			return source

	return bom_rows["by_item"].get(work_order_item.get("item_code"))
