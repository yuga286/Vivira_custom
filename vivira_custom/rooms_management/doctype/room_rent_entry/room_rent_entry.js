frappe.ui.form.on("Room Rent Entry", {
	refresh(frm) {
		if (frm.doc.docstatus === 0 && !frm.is_new()) {
			frm.add_custom_button(__("Get Room Rent"), () => {
				frm.call({
					doc: frm.doc,
					method: "get_room_rent",
					freeze: true,
					freeze_message: __("Fetching Room Rent"),
				}).then((r) => {
					frm.dirty();
					frm.refresh_field("room_rents");
					frm.refresh_field("number_of_room_rents");
					frm.refresh_field("total_rent_amount");
					frm.scroll_to_field("room_rents");

					if (r.message) {
						frappe.show_alert({
							message: __("Fetched {0} Room Rent record(s)", [
								r.message.number_of_room_rents,
							]),
							indicator: "green",
						});
					}
				});
			}).toggleClass("btn-primary", !(frm.doc.room_rents || []).length);
		}

		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Room Rent Slips"), () => {
				frappe.set_route("List", "Room Rent Slip", {
					room_rent_entry: frm.doc.name,
				});
			});

			if (!frm.doc.room_rent_slips_created) {
				frm.add_custom_button(__("Create Room Rent Slips"), () => {
					frm.call({
						doc: frm.doc,
						method: "create_room_rent_slips",
						freeze: true,
						freeze_message: __("Creating Room Rent Slips"),
					}).then(() => {
						frm.reload_doc();
					});
				}).addClass("btn-primary");
			}
		}
	},
});
