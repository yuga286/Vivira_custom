import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def before_migrate():
	create_module_def()


def after_migrate():
	create_module_def()
	create_roles()
	create_custom_fields_for_fuel_management()
	create_indexes()
	ensure_fuel_register_report_access()
	ensure_workspace_for_desk()


def create_module_def():
	if not frappe.db.exists("Module Def", "Vehicle Fuel Management"):
		frappe.get_doc(
			{
				"doctype": "Module Def",
				"module_name": "Vehicle Fuel Management",
				"app_name": "vivira_custom",
				"custom": 0,
			}
		).insert(ignore_permissions=True)


def create_roles():
	for role in ("Fuel Manager", "Fuel User"):
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)


def create_custom_fields_for_fuel_management():
	custom_fields = {
		"Employee": [
			{
				"fieldname": "fuel_issue_history_section",
				"fieldtype": "Section Break",
				"label": "Issue History",
				"insert_after": "connections_tab",
				"collapsible": 1,
			},
			{
				"fieldname": "fuel_issue_history",
				"fieldtype": "Table",
				"label": "Issue History",
				"options": "Employee Fuel Issue History",
				"insert_after": "fuel_issue_history_section",
				"read_only": 1,
			},
		],
		"Vehicle": [
			{
				"fieldname": "fuel_owner_section",
				"fieldtype": "Section Break",
				"label": "Fuel Ownership",
				"insert_after": "employee",
				"collapsible": 1,
			},
			{
				"fieldname": "ownership_status",
				"fieldtype": "Select",
				"label": "Ownership Status",
				"options": "Own\nRental\nHired\nOther",
				"insert_after": "fuel_owner_section",
			},
			{
				"fieldname": "vehicle_supplier",
				"fieldtype": "Link",
				"label": "Vehicle Supplier",
				"options": "Supplier",
				"insert_after": "ownership_status",
			},
			{
				"fieldname": "owner_name",
				"fieldtype": "Data",
				"label": "Owner Name",
				"insert_after": "vehicle_supplier",
			},
			{
				"fieldname": "current_project",
				"fieldtype": "Link",
				"label": "Current Project",
				"options": "Project",
				"insert_after": "owner_name",
			},
		],
	}
	create_custom_fields(custom_fields, update=True)
	frappe.clear_cache(doctype="Employee")
	frappe.clear_cache(doctype="Vehicle")


def create_indexes():
	indexes = {
		"Fuel Ledger Entry": [
			["project", "fuel_type", "posting_date", "posting_time"],
			["voucher_type", "voucher_no"],
			["vehicle", "posting_date"],
			["employee", "posting_date"],
		],
		"Fuel Issue": [
			["project", "fuel_type", "posting_date"],
			["vehicle", "posting_date"],
			["employee", "posting_date"],
		],
		"Fuel Receipt": [["project", "fuel_type", "posting_date"], ["supplier", "posting_date"]],
	}
	for doctype, doctype_indexes in indexes.items():
		if frappe.db.table_exists(f"tab{doctype}"):
			for fields in doctype_indexes:
				frappe.db.add_index(doctype, fields)


def ensure_workspace_for_desk():
	if not frappe.db.exists("Workspace", "Vehicle Fuel Management"):
		return

	workspace = frappe.get_doc("Workspace", "Vehicle Fuel Management")
	workspace.db_set(
		{
			"app": "vivira_custom",
			"module": "Vehicle Fuel Management",
			"type": workspace.get("type") or "Workspace",
			"public": 1,
			"is_hidden": 0,
			"parent_page": "",
		},
		update_modified=False,
	)
	add_workspace_roles(workspace.name)
	ensure_workspace_report_links(workspace.name)
	workspace.reload()
	ensure_workspace_sidebar(workspace)
	frappe.clear_cache()


def ensure_fuel_register_report_access():
	report_name = "Vehicle Fuel Register"
	if not frappe.db.exists("Report", report_name):
		return

	frappe.db.set_value(
		"Report",
		report_name,
		{
			"module": "Vehicle Fuel Management",
			"report_type": "Script Report",
			"ref_doctype": "Fuel Issue",
			"is_standard": "Yes",
		},
		update_modified=False,
	)
	add_roles_to_parent(
		"Report",
		report_name,
		("System Manager", "Fuel Manager", "Fuel User", "Project Manager", "Projects User", "Accounts User"),
	)


def ensure_workspace_report_links(workspace_name):
	workspace = frappe.get_doc("Workspace", workspace_name)
	changed = False
	for child_table in ("links", "shortcuts"):
		for row in workspace.get(child_table, []):
			if row.get("link_to") != "Fuel Register":
				continue
			if child_table == "links" and row.get("link_type") != "Report":
				continue
			if child_table == "shortcuts" and row.get("type") != "Report":
				continue
			row.label = "Vehicle Fuel Register"
			row.link_to = "Vehicle Fuel Register"
			if row.meta.has_field("report_ref_doctype"):
				row.report_ref_doctype = "Fuel Issue"
			changed = True
	if changed:
		workspace.save(ignore_permissions=True)

	for doctype in ("Workspace Link", "Workspace Shortcut"):
		if not frappe.db.table_exists(f"tab{doctype}"):
			continue
		filters = {"parent": workspace_name, "link_to": "Fuel Register"}
		if doctype == "Workspace Link":
			filters["link_type"] = "Report"
		else:
			filters["type"] = "Report"
		for row in frappe.get_all(
			doctype,
			filters=filters,
			pluck="name",
		):
			values = {
				"label": "Vehicle Fuel Register",
				"link_to": "Vehicle Fuel Register",
				"report_ref_doctype": "Fuel Issue",
			}
			frappe.db.set_value(doctype, row, values, update_modified=False)
	frappe.db.commit()


def add_workspace_roles(workspace_name):
	add_roles_to_parent(
		"Workspace",
		workspace_name,
		("System Manager", "Fuel Manager", "Fuel User", "Project Manager", "Projects User", "Accounts User"),
	)


def add_roles_to_parent(parenttype, parent, roles):
	existing_roles = set(
		frappe.get_all(
			"Has Role",
			filters={"parenttype": parenttype, "parent": parent},
			pluck="role",
		)
	)
	for role in roles:
		if role not in existing_roles and frappe.db.exists("Role", role):
			frappe.get_doc(
				{
					"doctype": "Has Role",
					"parent": parent,
					"parenttype": parenttype,
					"parentfield": "roles",
					"role": role,
				}
			).insert(ignore_permissions=True)


def ensure_workspace_sidebar(workspace):
	if not frappe.db.exists("Workspace Sidebar", "Vehicle Fuel Management"):
		frappe.get_doc(
			{
				"doctype": "Workspace Sidebar",
				"title": workspace.title or workspace.name,
				"header_icon": workspace.icon or "fuel",
				"module": "Vehicle Fuel Management",
				"app": "vivira_custom",
				"standard": 1,
			}
		).insert(ignore_permissions=True)
	else:
		frappe.db.set_value(
			"Workspace Sidebar",
			"Vehicle Fuel Management",
			{
				"title": workspace.title or workspace.name,
				"header_icon": workspace.icon or "fuel",
				"module": "Vehicle Fuel Management",
				"app": "vivira_custom",
				"standard": 1,
			},
			update_modified=False,
		)

	frappe.db.delete("Workspace Sidebar Item", {"parent": "Vehicle Fuel Management"})
	for item in get_workspace_sidebar_items(workspace):
		item.update(
			{
				"doctype": "Workspace Sidebar Item",
				"parent": "Vehicle Fuel Management",
				"parenttype": "Workspace Sidebar",
				"parentfield": "items",
			}
		)
		frappe.get_doc(item).insert(ignore_permissions=True)


def get_workspace_sidebar_items(workspace):
	items = [
		{
			"label": "Home",
			"type": "Link",
			"link_type": "Workspace",
			"link_to": workspace.name,
			"icon": "home",
			"idx": 0,
		}
	]
	idx = 1
	for shortcut in workspace.get("shortcuts", []):
		if not shortcut.link_to or not shortcut.type:
			continue
		label = shortcut.label
		link_to = shortcut.link_to
		if shortcut.type == "Report" and shortcut.link_to == "Fuel Register":
			label = "Vehicle Fuel Register"
			link_to = "Vehicle Fuel Register"
		items.append(
			{
				"label": label,
				"type": "Link",
				"link_type": shortcut.type,
				"link_to": link_to,
				"idx": idx,
			}
		)
		idx += 1
	return items
