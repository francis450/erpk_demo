// Persistent demo banner on every desk page.
(() => {
	const ID = "erpk-demo-banner";
	const mount = () => {
		if (document.getElementById(ID) || !document.body) return;
		const bar = document.createElement("div");
		bar.id = ID;
		bar.setAttribute("role", "note");
		bar.innerHTML =
			'<span class="erpk-demo-dot"></span>' +
			"Demo system by ERP Kenya · sample data · " +
			'<a href="https://erpkenya.com" target="_blank" rel="noopener">erpkenya.com</a>';
		document.body.appendChild(bar);
		document.body.classList.add("erpk-demo");
	};
	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", mount);
	} else {
		mount();
	}
	$(document).on("page-change", mount);
})();
