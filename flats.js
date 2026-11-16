// Shared sample flats state for the prototype (live stack, master, Flats settings).
// This browser preview only walks through the flow; it does not calibrate FITS.
(function (w) {
  const LIBS = [
    { id: "nov8", date: "Nov 8, 2026", rig: "Backyard Newt", camera: "ZWO ASI2600MC Pro", scope: "600 mm Newtonian", filter: "Color (OSC)", note: "Focus locked, rotator 0°", n: 25, temp: "2 °C", bin: "1×1" },
    { id: "oct19", date: "Oct 19, 2026", rig: "Backyard Newt", camera: "ZWO ASI2600MC Pro", scope: "600 mm Newtonian", filter: "Color (OSC)", note: "Focus 2 clicks off, rotator 0°", n: 20, temp: "6 °C", bin: "1×1" },
    // Same rig and filter as nov8/oct19, but bin 2×2, so it must not match a 1×1 session.
    { id: "jul22", date: "Jul 22, 2026", rig: "Backyard Newt", camera: "ZWO ASI2600MC Pro", scope: "600 mm Newtonian", filter: "Color (OSC)", note: "Focus locked, rotator 0°", n: 18, temp: "8 °C", bin: "2×2" },
    { id: "amy15", date: "Nov 15, 2026", rig: "80 mm refractor", camera: "ZWO ASI533MC Pro", scope: "80 mm f/5 refractor", filter: "Ha 7 nm", note: "Focus locked, no rotator", n: 20, temp: "1 °C", bin: "1×1" },
    { id: "bea2", date: "Nov 2, 2026", rig: "EdgeHD 8 + 0.7×", camera: "ZWO ASI294MC Pro", scope: "Celestron EdgeHD 8 · 0.7×", filter: "Color (OSC)", note: "Focus locked, rotator 352°", n: 30, temp: "4 °C", bin: "1×1" },
    { id: "dana30", date: "Oct 30, 2026", rig: "RedCat 71 (OSC)", camera: "ZWO ASI533MC Pro", scope: "William Optics RedCat 71", filter: "Color (OSC)", note: "Focus locked, rotator 12°", n: 21, temp: "3 °C", bin: "1×1" },
  ];
  const SESSION_MATCH = { camera: "ZWO ASI2600MC Pro", filter: "Color", bin: "1×1", rig: "Backyard Newt" };
  const RIG_DEFAULTS = {
    justin: { mode: "library", lib: "nov8" },
    amy: { mode: "before", lib: "amy15" },
    bea: { mode: "library", lib: "bea2" },
    cy: { mode: "before", lib: null },
    dana: { mode: "library", lib: "dana30" },
    dana2: { mode: "after", lib: null },
    eli: { mode: "after", lib: null },
  };
  // Mutable per-rig picks. Starts as a copy of the defaults so the session method is never overwritten.
  const RIGS = {};
  Object.keys(RIG_DEFAULTS).forEach((id) => { RIGS[id] = Object.assign({}, RIG_DEFAULTS[id]); });
  // Possessive pronoun for "shot before ___ first sub". Cy is called out so we do not hardcode "her".
  const POSS = { justin: "his", amy: "her", bea: "her", cy: "their", dana: "her", dana2: "her", eli: "his" };
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
      lead: "Reuse saved flats from a past session, matched by scope, camera, filter, binning, and the focus / rotation note.",
      warn: "A mismatch in focus, rotation, binning, or dust will leave marks in the master. You can swap in a fresh set later; the app then re-stacks.",
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
    return `${lib.date} · ${lib.scope} · ${lib.camera} · ${lib.filter} · bin ${lib.bin} · ${lib.note}`;
  }
  function sameCamera(lib, want) {
    if (!want || !want.camera) return true;
    const a = (lib.camera || "").toLowerCase(), b = want.camera.toLowerCase();
    return a === b || a.includes(b) || b.includes(a.replace(/^zwo\s+/, ""));
  }
  function sameFilter(lib, want) {
    if (!want || !want.filter) return true;
    const a = (lib.filter || "").toLowerCase(), b = want.filter.toLowerCase();
    return a === b || a.startsWith(b) || b.startsWith(a);
  }
  function sameBin(lib, want) {
    if (!want || !want.bin) return true;
    return lib.bin === want.bin;
  }
  // Hard match: camera, filter, and bin. Focus / rotation is shown on each card so you can check it;
  // a different note does not hide a set that otherwise matches.
  function matchLib(want) {
    return LIBS.filter((l) => sameCamera(l, want) && sameFilter(l, want) && sameBin(l, want));
  }
  function getRig(id) { return Object.assign({}, RIG_DEFAULTS[id] || { mode: "after", lib: null }, RIGS[id] || {}); }
  function setRig(id, patch) {
    RIGS[id] = Object.assign({}, getRig(id), patch);
    return RIGS[id];
  }
  function possOf(id) { return POSS[id] || "their"; }
  function sessionLine(r, d) {
    if (d.mode === "library") {
      const lib = d.lib ? libById(d.lib) : null;
      return lib ? lib.date + " · " + lib.note : "Library flats";
    }
    if (d.mode === "before") {
      return `Session flats, shot before ${r.name}'s first sub (${possOf(r.id)})`;
    }
    return "Raw subs kept · flats pending";
  }
  function shortBadge(mode) {
    if (mode === "after") return { tone: "warn", text: "Flats pending" };
    if (mode === "before") return { tone: "ok", text: "From frame 1" };
    return { tone: "ok", text: "Library" };
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
  w.FLATS = { LIBS, RIG_DEFAULTS, RIGS, SESSION_MATCH, MODES, libById, libLine, matchLib, getRig, setRig, possOf, sessionLine, shortBadge, badge, parse, qs, HONEST: "This browser preview only walks through flats. The native app applies them to the real subs. Nothing here is a calibrated FITS." };
})(window);
