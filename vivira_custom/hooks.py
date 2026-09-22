app_name = "vivira_custom"
app_title = "for the room setup in the custoruction"
app_publisher = "vigisolvo"
app_description = "cunstruction app"
app_email = "vigisolvo@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "vivira_custom",
# 		"logo": "/assets/vivira_custom/logo.png",
# 		"title": "for the room setup in the custoruction",
# 		"route": "/vivira_custom",
# 		"has_permission": "vivira_custom.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/vivira_custom/css/vivira_custom.css"
# app_include_js = "/assets/vivira_custom/js/vivira_custom.js"

# include js, css files in header of web template
# web_include_css = "/assets/vivira_custom/css/vivira_custom.css"
# web_include_js = "/assets/vivira_custom/js/vivira_custom.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "vivira_custom/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"BOM": "public/js/manufacturing_dimensions.js",
	"Work Order": "public/js/manufacturing_dimensions.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "vivira_custom/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "vivira_custom.utils.jinja_methods",
# 	"filters": "vivira_custom.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "vivira_custom.install.before_install"
# after_install = "vivira_custom.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "vivira_custom.uninstall.before_uninstall"
# after_uninstall = "vivira_custom.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "vivira_custom.utils.before_app_install"
# after_app_install = "vivira_custom.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "vivira_custom.utils.before_app_uninstall"
# after_app_uninstall = "vivira_custom.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "vivira_custom.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "vivira_custom.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events
doc_events = {
	"Payment Entry": {
		"on_submit": "vivira_custom.rooms_management.payment.update_room_rent_slip_from_payment_entry",
		"on_cancel": "vivira_custom.rooms_management.payment.update_room_rent_slip_from_payment_entry",
	},
	"BOM": {
		"validate": "vivira_custom.manufacturing.dimensions.calculate_bom_dimensions",
	},
	"Work Order": {
		"validate": "vivira_custom.manufacturing.dimensions.calculate_work_order_dimensions",
	},
}

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			[
				"dt",
				"in",
				[
					"BOM Item",
					"Work Order Item",
				],
			],
			[
				"fieldname",
				"in",
				[
					"thickness_mm",
					"width_mm",
					"length_mm",
					"total_area_sqm",
					"unit_weight_kg_sqm",
					"total_weight_kg",
				],
			],
		],
	}
]

before_migrate = "vivira_custom.vehicle_fuel_management.setup.before_migrate"

after_migrate = [
	"vivira_custom.rooms_management.setup.ensure_room_rent_slip_payment_entry_field",
	"vivira_custom.vehicle_fuel_management.setup.after_migrate",
]

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"vivira_custom.tasks.all"
# 	],
# 	"daily": [
# 		"vivira_custom.tasks.daily"
# 	],
# 	"hourly": [
# 		"vivira_custom.tasks.hourly"
# 	],
# 	"weekly": [
# 		"vivira_custom.tasks.weekly"
# 	],
# 	"monthly": [
# 		"vivira_custom.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "vivira_custom.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
extend_doctype_class = {
	"Payment Entry": [
		"vivira_custom.accounts.employee_advance_payment_entry.ViviraEmployeeAdvancePaymentEntryMixin"
	],
}

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "vivira_custom.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "vivira_custom.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["vivira_custom.utils.before_request"]
# after_request = ["vivira_custom.utils.after_request"]

# Job Events
# ----------
# before_job = ["vivira_custom.utils.before_job"]
# after_job = ["vivira_custom.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"vivira_custom.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
