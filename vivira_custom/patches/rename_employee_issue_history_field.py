import frappe


def execute():
	ensure_issue_history_field()
	frappe.db.sql(
		"""
		update `tabEmployee Fuel Issue History`
		set parentfield = 'issue_history'
		where parenttype = 'Employee'
			and parentfield = 'fuel_issue_history'
		"""
	)
	frappe.clear_cache(doctype="Employee")


def ensure_issue_history_field():
	old_name = "Employee-fuel_issue_history"
	new_name = "Employee-issue_history"

	if frappe.db.exists("Custom Field", old_name) and not frappe.db.exists("Custom Field", new_name):
		frappe.rename_doc("Custom Field", old_name, new_name, force=True)

	if frappe.db.exists("Custom Field", new_name):
		field = frappe.get_doc("Custom Field", new_name)
		field.update(
			{
				"fieldname": "issue_history",
				"label": "Issue History",
				"fieldtype": "Table",
				"options": "Employee Fuel Issue History",
				"insert_after": "fuel_issue_history_section",
				"read_only": 1,
			}
		)
		field.save(ignore_permissions=True)
	else:
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Employee",
				"fieldname": "issue_history",
				"label": "Issue History",
				"fieldtype": "Table",
				"options": "Employee Fuel Issue History",
				"insert_after": "fuel_issue_history_section",
				"read_only": 1,
			}
		).insert(ignore_permissions=True)

	if frappe.db.exists("Custom Field", old_name):
		frappe.delete_doc("Custom Field", old_name, ignore_permissions=True, force=True)
