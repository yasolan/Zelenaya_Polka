document.querySelectorAll(".saved-address-btn").forEach(function (btn) {
  btn.addEventListener("click", function () {
    const addressInput = document.getElementById("address-input");
    const display = document.getElementById("address-display");
    const lat = document.getElementById("delivery-lat");
    const lon = document.getElementById("delivery-lon");
    if (addressInput) addressInput.value = btn.dataset.address || "";
    if (display) {
      display.textContent = btn.dataset.address || "—";
      display.classList.add("address-selected--ok");
    }
    if (lat) lat.value = btn.dataset.lat || "";
    if (lon) lon.value = btn.dataset.lon || "";
    ["entrance", "floor", "apartment", "intercom"].forEach(function (key) {
      const el = document.querySelector('[name="' + key + '"]');
      if (el) el.value = btn.dataset[key] || "";
    });
  });
});
