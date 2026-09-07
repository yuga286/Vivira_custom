from contextlib import contextmanager

import frappe
from frappe.utils import flt


VALID_EMPLOYEE_ADVANCE_STATUSES_FOR_PAYMENT = {"Unpaid", "Partially Paid"}


class ViviraEmployeeAdvancePaymentEntryMixin:
	def validate(self):
		with allow_valid_employee_advance_receivable_gl_entries():
			super().validate()

	def make_gl_entries(self, cancel=0, adv_adj=0):
		with allow_valid_employee_advance_receivable_gl_entries():
			super().make_gl_entries(cancel=cancel, adv_adj=adv_adj)


@contextmanager
def allow_valid_employee_advance_receivable_gl_entries():
	"""Allow Employee parties on their own Employee Advance receivable account only."""
	from erpnext.accounts import party as party_module
	from erpnext.accounts.doctype.gl_entry import gl_entry as gl_entry_module

	original_party_validator = party_module.validate_account_party_type
	original_gl_validator = gl_entry_module.validate_account_party_type
	construction_accounting_module = get_construction_accounting_module()
	original_construction_party_fields = (
		construction_accounting_module.get_party_fields_for_account
		if construction_accounting_module
		else None
	)

	def validate_account_party_type(gl_entry):
		if is_valid_employee_advance_receivable_gl_entry(gl_entry):
			return

		return original_party_validator(gl_entry)

	def get_party_fields_for_account(account, transaction=None, party_type=None, party=None):
		if is_valid_employee_advance_payment_transaction(transaction, account, party_type, party):
			return {"party_type": "Employee", "party": party or transaction.party}

		return original_construction_party_fields(
			account,
			transaction=transaction,
			party_type=party_type,
			party=party,
		)

	party_module.validate_account_party_type = validate_account_party_type
	gl_entry_module.validate_account_party_type = validate_account_party_type
	if construction_accounting_module:
		construction_accounting_module.get_party_fields_for_account = get_party_fields_for_account

	try:
		yield
	finally:
		party_module.validate_account_party_type = original_party_validator
		gl_entry_module.validate_account_party_type = original_gl_validator
		if construction_accounting_module:
			construction_accounting_module.get_party_fields_for_account = original_construction_party_fields


def get_construction_accounting_module():
	try:
		from construction_management.construction_management.utils import accounting

		return accounting
	except (ImportError, AttributeError):
		return None


def is_valid_employee_advance_receivable_gl_entry(gl_entry) -> bool:
	if (
		gl_entry.get("voucher_type") != "Payment Entry"
		or not gl_entry.get("voucher_no")
		or gl_entry.get("party_type") != "Employee"
		or not gl_entry.get("party")
		or not gl_entry.get("company")
		or not gl_entry.get("account")
		or gl_entry.get("advance_voucher_type") != "Employee Advance"
		or not gl_entry.get("advance_voucher_no")
	):
		return False

	payment_entry = frappe.get_doc("Payment Entry", gl_entry.voucher_no)
	return is_valid_employee_advance_payment_account(
		payment_entry, gl_entry.account, gl_entry.advance_voucher_no
	)


def is_valid_employee_advance_payment_transaction(transaction, account, party_type=None, party=None) -> bool:
	if (
		not transaction
		or transaction.doctype != "Payment Entry"
		or party_type != "Employee"
		or not (party or transaction.get("party"))
	):
		return False

	for row in transaction.get("references") or []:
		if row.reference_doctype != "Employee Advance" or not row.reference_name:
			continue

		if is_valid_employee_advance_payment_account(transaction, account, row.reference_name):
			return True

	return False


def is_valid_employee_advance_payment_account(payment_entry, account: str, employee_advance: str) -> bool:
	if (
		payment_entry.doctype != "Payment Entry"
		or payment_entry.payment_type != "Pay"
		or payment_entry.party_type != "Employee"
		or not payment_entry.party
		or not payment_entry.company
		or payment_entry.paid_to != account
	):
		return False

	account_details = frappe.db.get_value(
		"Account", account, ["account_type", "company", "is_group", "disabled"], as_dict=True
	)
	if (
		not account_details
		or account_details.account_type != "Receivable"
		or account_details.company != payment_entry.company
		or account_details.is_group
		or account_details.disabled
	):
		return False

	reference_names = {
		row.reference_name
		for row in payment_entry.get("references")
		if row.reference_doctype == "Employee Advance" and row.reference_name and flt(row.allocated_amount)
	}
	if employee_advance not in reference_names:
		return False

	advance = frappe.db.get_value(
		"Employee Advance",
		employee_advance,
		["employee", "company", "advance_account", "docstatus", "status"],
		as_dict=True,
	)
	if not advance:
		return False

	if (
		advance.employee != payment_entry.party
		or advance.company != payment_entry.company
		or advance.advance_account != account
		or advance.docstatus != 1
	):
		return False

	if payment_entry.docstatus == 0 and advance.status not in VALID_EMPLOYEE_ADVANCE_STATUSES_FOR_PAYMENT:
		return False

	return True
