frappe.ui.form.on("Fuel Receipt", {
	setup(frm) {
		frm.set_query("fuel_type", () => ({ filters: { disabled: 0 } }));
	},

	refresh(frm) {
		frm.trigger("set_total_amount");
	},

	qty(frm) {
		frm.trigger("set_total_amount");
	},

	unit_rate(frm) {
		frm.trigger("set_total_amount");
	},

	fuel_type(frm) {
		if (frm.doc.fuel_type && !frm.doc.uom) {
			frappe.db.get_value("Item", frm.doc.fuel_type, "stock_uom").then((r) => {
				frm.set_value("uom", r.message?.stock_uom);
			});
		}
	},

	set_total_amount(frm) {
		frm.set_value("total_amount", flt(frm.doc.qty) * flt(frm.doc.unit_rate));
	},
});
