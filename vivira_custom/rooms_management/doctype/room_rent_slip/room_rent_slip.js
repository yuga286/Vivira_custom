frappe.ui.form.on("Room Rent Slip", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && flt(frm.doc.outstanding_amount) > 0) {
			frm.add_custom_button(__("Make Payment"), () => {
				frappe.model.with_doctype("Payment Entry", () => {
					const payment_entry = frappe.model.get_new_doc("Payment Entry");
					payment_entry.payment_type = "Pay";
					payment_entry.party_type = "Supplier";
					payment_entry.party = frm.doc.supplier;
					payment_entry.paid_amount = frm.doc.outstanding_amount;
					payment_entry.received_amount = frm.doc.outstanding_amount;
					payment_entry.custom_room_rent_slip = frm.doc.name;
					frappe.set_route("Form", "Payment Entry", payment_entry.name);
				});
			}).addClass("btn-primary");
		}
	},
});
