frappe.ui.form.on("Material Issued", {
	setup(frm) {
		frm.set_query("item", () => ({ filters: { disabled: 0 } }));
	},

	employee(frm) {
		if (!frm.doc.employee) {
			frm.set_value("employee_name", null);
			frm.set_value("subcontractor_supplier", null);
			frm.set_value("subcontractor_supplier_name", null);
			return;
		}

		frappe.db
			.get_value("Employee", frm.doc.employee, ["employee_name", "subcontractor_supplier"])
			.then((r) => {
				const employee = r.message || {};
				frm.set_value("employee_name", employee.employee_name);
				frm.set_value("subcontractor_supplier", employee.subcontractor_supplier);
			});
	},

	subcontractor_supplier(frm) {
		if (!frm.doc.subcontractor_supplier) {
			frm.set_value("subcontractor_supplier_name", null);
			return;
		}

		frappe.db.get_value("Supplier", frm.doc.subcontractor_supplier, "supplier_name").then((r) => {
			frm.set_value("subcontractor_supplier_name", r.message?.supplier_name);
		});
	},

	item(frm) {
		if (!frm.doc.item) {
			frm.set_value("item_name", null);
			return;
		}

		frappe.db.get_value("Item", frm.doc.item, ["item_name", "stock_uom"]).then((r) => {
			const item = r.message || {};
			frm.set_value("item_name", item.item_name);
			if (!frm.doc.uom) frm.set_value("uom", item.stock_uom);
		});
	},
});
