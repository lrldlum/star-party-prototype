// Shared sample flats state for the prototype (live stack, master, Flats settings).
// This browser preview only walks through the flow; it does not calibrate FITS.
(function (w) {
  const LIBS = [
    { id: "nov8", date: "Nov 8, 2026", rig: "Backyard Newt", camera: "ZWO ASI2600MC Pro", scope: "600 mm Newtonian", filter: "Color (OSC)", note: "Focus locked, rotator 0°", n: 25, temp: "2 °C" },
    { id: "oct19", date: "Oct 19, 2026", rig: "Backyard Newt", camera: "ZWO ASI2600MC Pro", scope: "600 mm Newtonian", filter: "Color (OSC)", note: "Focus 2 clicks off, rotator 0°", n: 20, temp: "6 °C" },
    { id: "amy15", date: "Nov 15, 2026", rig: "80 mm refractor", camera: "ZWO ASI533MC Pro", scope: "80 mm f/5 refractor", filter: "Ha 7 nm", note: "Focus locked, no rotator", n: 20, temp: "1 °C" },
    { id: "bea2", date: "Nov 2, 2026", rig: "EdgeHD 8 + 0.7×", camera: "ZWO ASI294MC Pro", scope: "Celestron EdgeHD 8 · 0.7×", filter: "Color (OSC)", note: "Focus locked, rotator 352°", n: 30, temp: "4 °C" },
    { id: "dana30", date: "Oct 30, 2026", rig: "RedCat 71 (OSC)", camera: "ZWO ASI533MC Pro", scope: "William Optics RedCat 71", filter: "Color (OSC)", note: "Focus locked, rotator 12°", n: 21, temp: "3 °C" },
  ];
  const RIG_DEFAULTS = {
    justin: { mode: "library", lib: "nov8" },
    amy: { mode: "before", lib: "amy15" },
    bea: { mode: "library", lib: "bea2" },
    cy: { mode: "before", lib: null },
    dana: { mode: "library", lib: "dana30" },
    dana2: { mode: "after", lib: null },
    eli: { mode: "after", lib: null },
  };
  const MODES = {
    before: {
      k: "before",
      title: "Flats before the session",
      short: "Session flats",
      lead: "Shoot or load flats first. Every incoming sub is calibrated live, so the live master is correct from frame 1.",
      warn: "After these flats, don't change focus, rotation, or the camera. If you do, shoot a fresh set.",
    },
    library: {
      k: "library",
      title: "Flat library",
      short: "Library flats",
      lead: "Reuse saved flats from a past session, matched by scope, camera, filter, and the focus / rotation note.",
      warn: "A mismatch in focus, rotation, or dust will leave marks in the master. You can swap in a fresh set later; the app then re-stacks.",
    },
    after: {
      k: "after",
      title: "Flats after (traditional)",
      short: "Flats after",
      lead: "The live stack runs uncalibrated. Raw subs are kept. When you add flats, the app re-stacks everything calibrated and replaces the master.",
      warn: "The live preview will show vignetting and dust until flats go in. That's expected.",
    },
  };
  function libById(id) { return LIBS.find((x) => x.id === id) || LIBS[0]; }
  function libLine(lib) {
    if (!lib) return "";
    return `${lib.date} · ${lib.scope} · ${lib.camera} · ${lib.filter} · ${lib.note}`;
  }
  function badge(mode, restack, lib) {
    const L = typeof lib === "string" ? libById(lib) : lib;
    if (restack === "progress") return { tone: "prog", text: "Re-stacking with flats…", detail: "Raw subs are being calibrated and stacked again. The master will be replaced when this finishes. Simulated." };
    if (restack === "done") {
      if (mode === "library") return { tone: "ok", text: `Calibrated · fresh library flats${L ? " · " + L.date : ""}`, detail: L ? `Applied ${libLine(L)}. The previous master was replaced. Simulated.` : "The previous master was replaced. Simulated." };
      return { tone: "ok", text: "Calibrated · flats added tonight", detail: "Raw subs were kept and the master was replaced with a calibrated stack. Simulated." };
    }
    if (mode === "before") return { tone: "ok", text: "Calibrated from frame 1 · session flats", detail: MODES.before.warn };
    if (mode === "library") return { tone: "ok", text: `Calibrated · library flats${L ? " · " + L.date : ""}`, detail: L ? libLine(L) : MODES.library.lead };
    if (mode === "after") return { tone: "warn", text: "Uncalibrated, flats pending", detail: "Raw subs are kept. Add flats to re-stack a calibrated master." };
    return null;
  }
  function parse(hash) {
    const q = new URLSearchParams((hash || "").replace(/^#/, ""));
    const mode = ["before", "library", "after"].includes(q.get("flats")) ? q.get("flats") : (["before", "library", "after"].includes(q.get("mode")) ? q.get("mode") : null);
    const restack = ["progress", "done"].includes(q.get("restack")) ? q.get("restack") : null;
    const lib = LIBS.some((x) => x.id === q.get("lib")) ? q.get("lib") : (mode === "library" ? "nov8" : null);
    const view = q.get("view");
    const who = q.get("who");
    return { mode, restack, lib, view, who };
  }
  function qs(state, extra) {
    const q = new URLSearchParams();
    const s = Object.assign({}, state, extra);
    if (s.mode) q.set("flats", s.mode);
    if (s.lib && s.mode === "library") q.set("lib", s.lib);
    if (s.restack) q.set("restack", s.restack);
    if (s.view) q.set("view", s.view);
    if (s.who) q.set("who", s.who);
    const str = q.toString();
    return str ? "#" + str : "";
  }
  w.FLATS = { LIBS, RIG_DEFAULTS, MODES, libById, libLine, badge, parse, qs, HONEST: "This browser preview only walks through flats. The native app applies them to the real subs. Nothing here is a calibrated FITS." };
})(window);
