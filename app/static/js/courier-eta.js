(function () {
  const panel = document.getElementById("courier-eta-panel");
  const el = document.getElementById("courier-eta-countdown");
  if (!panel || !el || !panel.dataset.deadline) return;

  const deadline = new Date(panel.dataset.deadline).getTime();

  function tick() {
    const left = deadline - Date.now();
    if (left <= 0) {
      el.textContent = "скоро";
      panel.classList.add("courier-eta-panel--done");
      return;
    }
    const totalSec = Math.floor(left / 1000);
    const min = Math.floor(totalSec / 60);
    const sec = totalSec % 60;
    if (min >= 60) {
      const h = Math.floor(min / 60);
      const m = min % 60;
      el.textContent = h + " ч " + m + " мин";
    } else {
      el.textContent = min + " мин " + (sec < 10 ? "0" : "") + sec + " сек";
    }
  }

  tick();
  setInterval(tick, 1000);
})();
