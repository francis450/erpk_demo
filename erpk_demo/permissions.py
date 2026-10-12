import frappe


def user_query_conditions(user=None):
	"""On a demo site, people without System Manager see only their own User record.
	Frappe core would otherwise list every user to any desk user."""
	user = user or frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""
	return f"`tabUser`.name = {frappe.db.escape(user)}"


def user_has_permission(doc, ptype=None, user=None):
	user = user or frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return None
	return doc.name == user
