frappe.ui.form.on("Fuel Issue", {
	setup(frm) {
		frm.set_query("fuel_type", () => ({ filters: { disabled: 0 } }));
	},

	refresh(frm) {
		frm.trigger("update_balance");
		frm.trigger("calculate_mileage");
	},

	project(frm) {
		frm.trigger("update_balance");
	},

	fuel_type(frm) {
		if (frm.doc.fuel_type && !frm.doc.uom) {
			frappe.db.get_value("Item", frm.doc.fuel_type, "stock_uom").then((r) => {
				frm.set_value("uom", r.message?.stock_uom);
			});
		}
		frm.trigger("update_balance");
	},

	posting_date(frm) {
		frm.trigger("update_balance");
	},

	posting_time(frm) {
		frm.trigger("update_balance");
	},

	qty_issued(frm) {
		frm.trigger("calculate_mileage");
	},

	current_odometer_reading(frm) {
		frm.trigger("calculate_mileage");
	},

	vehicle(frm) {
		if (!frm.doc.vehicle) return;
		frappe.db
			.get_value("Vehicle", frm.doc.vehicle, [
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
			])
			.then((r) => {
				const v = r.message || {};
				frm.set_value("vehicle_no", v.license_plate || frm.doc.vehicle);
				frm.set_value("vehicle_name", [v.make, v.model].filter(Boolean).join(" "));
				if (!frm.doc.employee) frm.set_value("employee", v.employee);
				if (!frm.doc.fuel_type && v.fuel_type) {
					frappe.db.exists("Item", v.fuel_type).then((exists) => {
						if (exists) frm.set_value("fuel_type", v.fuel_type);
					});
				}
				if (!frm.doc.uom) frm.set_value("uom", v.uom);
				if (!frm.doc.project) frm.set_value("project", v.current_project);
				if (!frm.doc.vehicle_status) frm.set_value("vehicle_status", v.ownership_status);
				if (!frm.doc.supplier) frm.set_value("supplier", v.vehicle_supplier);
				if (!frm.doc.owner_name) frm.set_value("owner_name", v.owner_name);
				frm.trigger("update_balance");
			});
	},

	employee(frm) {
		if (!frm.doc.employee) return;
		frappe.db.get_value("Employee", frm.doc.employee, "employee_name").then((r) => {
			frm.set_value("employee_name", r.message?.employee_name);
		});
	},

	supplier(frm) {
		if (frm.doc.owner_type !== "Supplier" || !frm.doc.supplier) return;
		frappe.db.get_value("Supplier", frm.doc.supplier, "supplier_name").then((r) => {
			frm.set_value("owner_name", r.message?.supplier_name);
		});
	},

	update_balance(frm) {
		if (!(frm.doc.project && frm.doc.fuel_type)) return;
		frappe.call({
			method: "vivira_custom.vehicle_fuel_management.fuel_stock.get_project_fuel_balance",
			args: {
				project: frm.doc.project,
				fuel_type: frm.doc.fuel_type,
				posting_date: frm.doc.posting_date,
				posting_time: frm.doc.posting_time,
				exclude_voucher_no: frm.doc.__islocal ? null : frm.doc.name,
			},
			callback(r) {
				frm.set_value("available_qty", r.message || 0);
			},
		});
	},

	calculate_mileage(frm) {
		if (!flt(frm.doc.previous_odometer_reading)) {
			frm.set_value("distance_travelled", 0);
			frm.set_value("average_mileage", 0);
			return;
		}
		const distance = flt(frm.doc.current_odometer_reading) - flt(frm.doc.previous_odometer_reading);
		frm.set_value("distance_travelled", distance > 0 ? distance : 0);
		frm.set_value(
			"average_mileage",
			distance > 0 && flt(frm.doc.qty_issued) > 0 ? distance / flt(frm.doc.qty_issued) : 0
		);
	},
});
