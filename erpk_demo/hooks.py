app_name = "erpk_demo"
app_title = "ERPK Demo"
app_publisher = "ERP Kenya"
app_description = "ERP Kenya prospect demo app (resettable, profile-driven demo data)"
app_email = "contact@erpkenya.com"
app_license = "mit"

required_apps = ["erpnext"]

app_logo_url = "/assets/erpk_demo/images/erpkenya-logo.png"

# Desk: demo banner + brand colours on every page
app_include_js = "/assets/erpk_demo/js/erpk_demo_banner.js"
app_include_css = "/assets/erpk_demo/css/erpk_demo.css"

# Est. unit cost / margin while pricing
doctype_js = {"Quotation": "public/js/quotation.js"}

# Website: send visitors straight to login
home_page = "login"

# Demo users see only their own User record
permission_query_conditions = {"User": "erpk_demo.permissions.user_query_conditions"}
has_permission = {"User": "erpk_demo.permissions.user_has_permission"}

after_install = "erpk_demo.install.after_install"

# Only records owned by this app. Prospect data is seed, never fixtures.
fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			["dt", "in", ["Quotation", "Quotation Item", "Sales Order Item"]],
			["fieldname", "like", "erpk_%"],
		],
	},
	{
		"dt": "Property Setter",
		"filters": [
			["doc_type", "in", ["Quotation", "Quotation Item", "Sales Order Item"]],
			["field_name", "like", "erpk_%"],
		],
	},
	{"dt": "Custom HTML Block", "filters": [["name", "like", "ERPK %"]]},
	{"dt": "Number Card", "filters": [["module", "=", "ERPK Demo"]]},
	{"dt": "Dashboard Chart", "filters": [["module", "=", "ERPK Demo"]]},
	{"dt": "Workspace", "filters": [["name", "=", "Workshop"]]},
	{"dt": "Print Format", "filters": [["name", "like", "ERPK %"]]},
	{"dt": "Role Profile", "filters": [["name", "=", "ERPK Demo User"]]},
	{"dt": "Module Profile", "filters": [["name", "=", "ERPK Demo Modules"]]},
]
fixture_auto_order = True
