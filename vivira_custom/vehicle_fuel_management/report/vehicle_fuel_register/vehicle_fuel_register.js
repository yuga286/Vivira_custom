const vehicle_fuel_register_months = [
	"January",
	"February",
	"March",
	"April",
	"May",
	"June",
	"July",
	"August",
	"September",
	"October",
	"November",
	"December",
];

frappe.query_reports["Vehicle Fuel Register"] = {
	filters: [
		{ fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company", reqd: 1 },
		{ fieldname: "project", label: __("Project"), fieldtype: "Link", options: "Project", reqd: 1 },
		{ fieldname: "vehicle", label: __("Vehicle"), fieldtype: "Link", options: "Vehicle" },
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: vehicle_fuel_register_months.join("\n"),
			default: vehicle_fuel_register_months[new Date().getMonth()],
			reqd: 1,
		},
		{
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Int",
			default: new Date().getFullYear(),
			reqd: 1,
		},
	],

	onload(report) {
		report.page.add_inner_button(__("Download Excel"), () => {
			const filters = report.get_filter_values(true);
			open_url_post(
				"/api/method/vivira_custom.vehicle_fuel_management.report.vehicle_fuel_register.vehicle_fuel_register.download_excel",
				{ filters: JSON.stringify(filters) }
			);
		});
	},

	refresh() {
		setTimeout(render_fuel_register_html, 0);
	},

	formatter(value, row, column, data, default_formatter) {
		if (column.fieldname === "html") {
			return value || "";
		}
		return default_formatter(value, row, column, data);
	},

	after_datatable_render() {
		render_fuel_register_html();
	},
};

function render_fuel_register_html() {
	const report = frappe.query_report;
	if (!report || !report.page || !report.data || !report.data.length) return;

	const html = report.data[0].html || "";
	const wrapper = report.page.main.find(".report-wrapper");
	if (!wrapper.length) return;

	wrapper.addClass("vehicle-fuel-register-report");
	wrapper.find(".vehicle-fuel-register-display").remove();
	wrapper.find(".datatable").hide();
	wrapper.prepend(`<div class="vehicle-fuel-register-display report-html">${html}</div>`);
}
