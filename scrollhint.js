// Scroll hint for prototype panels: a soft fade + "More below" at the fold while a panel has more content
// under it, so a card or link cut by the fold reads as "scroll for more". Hidden at the bottom.
(function () {
  const css = document.createElement("style");
  css.textContent = ".sfade{position:sticky;bottom:var(--sf-b,-12px);height:30px;margin-top:-30px;pointer-events:none;flex-shrink:0;" +
    "background:linear-gradient(rgba(7,16,24,0),rgba(7,16,24,.94) 75%);display:flex;align-items:flex-end;justify-content:center;transition:opacity .2s;z-index:3}" +
    ".sfade span{font:600 11px Inter,-apple-system,sans-serif;color:#8FA3B5;background:#0E1A26;border:1px solid #1C2B3A;border-radius:999px;padding:1px 9px;margin-bottom:2px}" +
    ".sfade.off{opacity:0}";
  document.head.appendChild(css);
  function attach(p) {
    if (p._sf) return; const f = document.createElement("div"); f.className = "sfade off"; f.setAttribute("aria-hidden", "true");
    f.innerHTML = "<span>More below ↓</span>"; p.appendChild(f); p._sf = f;
    f.style.setProperty("--sf-b", "-" + (parseFloat(getComputedStyle(p).paddingBottom) || 0) + "px");
    const upd = () => { if (f !== p.lastElementChild) p.appendChild(f); f.classList.toggle("off", p.scrollHeight - p.clientHeight - p.scrollTop < 24); };
    p.addEventListener("scroll", upd, { passive: true }); new ResizeObserver(upd).observe(p);
    new MutationObserver(() => requestAnimationFrame(upd)).observe(p, { childList: true, subtree: true, attributes: true, attributeFilter: ["hidden", "class", "style"] });
    upd();
  }
  const go = () => document.querySelectorAll(".panel, .sheet-body").forEach(attach);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go); else go();
})();
