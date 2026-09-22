(function () {
	function get_number(value) {
		return flt(value || 0);
	}

	function calculate_dimensions(row, qty_field) {
		const total_area =
			(get_number(row.width_mm) * get_number(row.length_mm) * get_number(row[qty_field])) / 1000000;
		return {
			total_area_sqm: flt(total_area, 6),
			total_weight_kg: flt(total_area * get_number(row.unit_weight_kg_sqm), 6),
		};
	}

	function update_child_dimensions(cdt, cdn, qty_field) {
		const row = locals[cdt] && locals[cdt][cdn];
		if (!row) return;

		const values = calculate_dimensions(row, qty_field);
		frappe.model.set_value(cdt, cdn, "total_area_sqm", values.total_area_sqm);
		frappe.model.set_value(cdt, cdn, "total_weight_kg", values.total_weight_kg);
	}

	["width_mm", "length_mm", "qty", "unit_weight_kg_sqm"].forEach((fieldname) => {
		frappe.ui.form.on("BOM Item", fieldname, function (frm, cdt, cdn) {
			update_child_dimensions(cdt, cdn, "qty");
		});
	});

	["width_mm", "length_mm", "required_qty", "unit_weight_kg_sqm"].forEach((fieldname) => {
		frappe.ui.form.on("Work Order Item", fieldname, function (frm, cdt, cdn) {
			update_child_dimensions(cdt, cdn, "required_qty");
		});
	});
})();
