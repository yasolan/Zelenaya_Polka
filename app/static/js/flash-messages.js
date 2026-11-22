(function () {
  const SUCCESS_MS = 1000;
  const ERROR_MS = 1000;

  function dismissFlash(el) {
    if (!el || el.classList.contains("flash--hiding")) return;
    el.classList.add("flash--hiding");
    window.setTimeout(() => {
      el.remove();
      const list = el.closest(".flash-messages");
      if (list && !list.children.length) list.remove();
    }, 180);
  }

  function init() {
    document.querySelectorAll(".flash-messages .flash").forEach((el) => {
      const isError = el.classList.contains("flash-error");
      const delay = isError ? ERROR_MS : SUCCESS_MS;
      window.setTimeout(() => dismissFlash(el), delay);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
