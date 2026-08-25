frappe.listview_settings["Room Rent Slip"] = {
	get_indicator(doc) {
		if (doc.payment_status === "Paid") {
			return [__("Paid"), "green", "payment_status,=,Paid"];
		}
		if (doc.payment_status === "Partially Paid") {
			return [__("Partially Paid"), "orange", "payment_status,=,Partially Paid"];
		}
		return [__("Unpaid"), "red", "payment_status,=,Unpaid"];
	},
};
