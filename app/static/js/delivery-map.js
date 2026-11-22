(function () {
  const mapEl = document.getElementById("delivery-map");
  if (!mapEl || typeof L === "undefined") return;

  let data = { center: { lat: 59.22, lon: 39.92, zoom: 12 }, zone: [], stores: [] };
  const raw = document.getElementById("delivery-map-data");
  if (raw && raw.textContent) {
    try {
      data = JSON.parse(raw.textContent);
    } catch (e) {
      console.warn("delivery-map-data parse error", e);
    }
  }

  const addressInput = document.getElementById("address-input");
  const addressDisplay = document.getElementById("address-display");
  const latInput = document.getElementById("delivery-lat");
  const lonInput = document.getElementById("delivery-lon");
  const zoneHint = document.getElementById("zone-status");
  const interactive = mapEl.dataset.interactive === "1";

  const map = L.map(mapEl, {
    scrollWheelZoom: true,
    attributionControl: false,
  }).setView([data.center.lat, data.center.lon], data.center.zoom);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "",
    maxZoom: 19,
  }).addTo(map);

  function ringToLatLngs(ring) {
    return ring.map(function (c) {
      return [c[1], c[0]];
    });
  }

  function pointInRing(lon, lat, ring) {
    if (!ring || ring.length < 3) return true;
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const xi = ring[i][0];
      const yi = ring[i][1];
      const xj = ring[j][0];
      const yj = ring[j][1];
      const intersect =
        yi > lat !== yj > lat &&
        lon < ((xj - xi) * (lat - yi)) / (yj - yi + 1e-15) + xi;
      if (intersect) inside = !inside;
    }
    return inside;
  }

  if (data.zone && data.zone.length) {
    const poly = L.polygon(ringToLatLngs(data.zone), {
      color: "#c44",
      weight: 2,
      fillColor: "#8B9A6E",
      fillOpacity: 0.22,
    }).addTo(map);
    map.fitBounds(poly.getBounds(), { padding: [24, 24] });
  }

  const storeIcon = L.divIcon({
    className: "store-marker",
    html: '<span>🥬</span>',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });

  (data.stores || []).forEach(function (store) {
    L.marker([store.lat, store.lon], { icon: storeIcon })
      .addTo(map)
      .bindPopup(
        "<strong>" +
          (store.name || "Зелёная полка") +
          "</strong><br>" +
          (store.address || "")
      );
  });

  let deliveryMarker = null;

  function setZoneStatus(inside) {
    if (!zoneHint) return;
    zoneHint.classList.remove("flash-error", "flash-success");
    if (inside) {
      zoneHint.textContent = "Точка в зоне доставки — можно оформлять заказ.";
      zoneHint.classList.add("flash-success");
    } else {
      zoneHint.textContent = "Вне зоны доставки. Выберите адрес внутри контура на карте.";
      zoneHint.classList.add("flash-error");
    }
    zoneHint.style.display = "block";
  }

  function applyPoint(lat, lon) {
    if (latInput) latInput.value = String(lat);
    if (lonInput) lonInput.value = String(lon);
    const inside = pointInRing(lon, lat, data.zone);
    setZoneStatus(inside);
    if (!inside) return;

    fetch(
      "https://nominatim.openstreetmap.org/reverse?format=json&lat=" +
        encodeURIComponent(lat) +
        "&lon=" +
        encodeURIComponent(lon) +
        "&accept-language=ru",
      { headers: { Accept: "application/json" } }
    )
      .then(function (r) {
        return r.json();
      })
      .then(function (json) {
        if (json.display_name) {
          if (addressInput) addressInput.value = json.display_name;
          if (addressDisplay) {
            addressDisplay.textContent = json.display_name;
            addressDisplay.classList.add("address-selected--ok");
          }
        }
      })
      .catch(function () {});
  }

  if (interactive) {
    const deliveryIcon = L.divIcon({
      className: "delivery-marker",
      html: '<span>📍</span>',
      iconSize: [28, 28],
      iconAnchor: [14, 28],
    });

    map.on("click", function (e) {
      const { lat, lng } = e.latlng;
      if (!deliveryMarker) {
        deliveryMarker = L.marker([lat, lng], {
          icon: deliveryIcon,
          draggable: true,
        }).addTo(map);
        deliveryMarker.on("dragend", function () {
          const p = deliveryMarker.getLatLng();
          applyPoint(p.lat, p.lng);
        });
      } else {
        deliveryMarker.setLatLng([lat, lng]);
      }
      applyPoint(lat, lng);
    });
  }
})();
