// Shared keyboard and dialog helpers for the interactive prototype screens.
(function () {
  function isOpen(el) { return el && !el.hidden; }
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const sheet = document.getElementById("sheet");
    const dlg = document.getElementById("dlg");
    if (isOpen(sheet)) {
      e.preventDefault();
      const x = document.getElementById("shX");
      if (x) x.click();
    } else if (isOpen(dlg)) {
      e.preventDefault();
      const n = document.getElementById("dNo");
      if (n) n.click();
    }
  });
})();
