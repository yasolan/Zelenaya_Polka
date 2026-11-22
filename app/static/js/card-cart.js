(function () {
  function formatQty(value, step) {
    const n = Number(value);
    if (!Number.isFinite(n) || n <= 0) return "0";
    if (step >= 1) return String(Math.round(n));
    const rounded = Math.round(n * 10) / 10;
    if (Math.abs(rounded - Math.round(rounded)) < 1e-6) {
      return String(Math.round(rounded));
    }
    return rounded.toFixed(1).replace(".", ",");
  }

  function updateCartBadge(count) {
    const link = document.querySelector(".nav-icon--cart");
    if (!link) return;
    let badge = link.querySelector(".badge--nav");
    const n = Number(count) || 0;
    if (n > 0) {
      if (!badge) {
        badge = document.createElement("span");
        badge.className = "badge badge--nav";
        link.appendChild(badge);
      }
      badge.textContent = String(n);
    } else if (badge) {
      badge.remove();
    }
  }

  function showStockNotice(message) {
    if (!message) return;
    const main = document.querySelector("main");
    if (!main) return;
    let ul = main.querySelector(".flash-messages");
    if (!ul) {
      ul = document.createElement("ul");
      ul.className = "flash-messages";
      main.insertBefore(ul, main.firstChild);
    }
    const li = document.createElement("li");
    li.className = "flash flash-error";
    li.textContent = message;
    ul.appendChild(li);
    setTimeout(() => li.remove(), 3200);
  }

  function setInCart(root, quantity) {
    const step = parseFloat(root.dataset.step) || 1;
    const stockMax = parseFloat(root.dataset.stockMax);
    const cta = root.querySelector(".card-cart__cta");
    const stepper = root.querySelector(".card-cart__stepper");
    const display = root.querySelector("[data-qty-display]");
    const plus = root.querySelector(".qty-stepper__btn--plus");
    const inCart = quantity > 0;
    const tableOnly = root.classList.contains("card-cart--table");
    const atMax = Number.isFinite(stockMax) && stockMax > 0 && quantity >= stockMax - 1e-9;

    if (display) display.textContent = formatQty(quantity, step);
    if (cta) cta.hidden = inCart;
    if (stepper) stepper.hidden = !inCart && !tableOnly;
    if (plus) {
      plus.disabled = atMax;
      plus.setAttribute("aria-disabled", atMax ? "true" : "false");
    }
  }

  function updateCartPageRow(root, data) {
    const row = root.closest("[data-cart-row]");
    if (!row) return;
    const lineCell = row.querySelector("[data-line-total]");
    const totalEl = document.querySelector("[data-cart-total]");
    if (data.quantity <= 0) {
      row.remove();
      const tbody = document.querySelector("#cart-table tbody");
      if (tbody && !tbody.children.length) {
        window.location.reload();
      }
    } else if (lineCell && data.line_total != null) {
      lineCell.textContent = `${Math.round(data.line_total)} ₽`;
    }
    if (totalEl && data.cart_total != null) {
      totalEl.innerHTML = `Итого: <strong>${Math.round(data.cart_total)} ₽</strong>`;
    }
  }

  async function postCart(root, action) {
    const url = root.dataset.cartUrl;
    if (!url) return;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ action }),
      credentials: "same-origin",
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      if (data && data.message) showStockNotice(data.message);
      else if (data && data.error === "out_of_stock") showStockNotice("Нет на складе.");
      return;
    }
    setInCart(root, data.quantity);
    updateCartBadge(data.cart_count);
    updateCartPageRow(root, data);
    if (data.message) showStockNotice(data.message);
  }

  function onClick(event) {
    const root = event.target.closest(".card-cart");
    if (!root) return;
    if (event.target.closest(".card-cart__cta")) {
      event.preventDefault();
      postCart(root, "add");
      return;
    }
    if (event.target.closest(".qty-stepper__btn--plus")) {
      event.preventDefault();
      postCart(root, "plus");
      return;
    }
    if (event.target.closest(".qty-stepper__btn--minus")) {
      event.preventDefault();
      postCart(root, "minus");
    }
  }

  document.addEventListener("click", onClick);
})();
