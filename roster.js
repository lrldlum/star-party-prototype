// One sample roster for every prototype screen (sample data). Master tab credits (rig chips per filter) and the
// Sky view frames both come from here, so the two always list the same members and rigs.
// filters: which master each rig's subs land in (grouped by the FITS FILTER header; one-shot-color subs -> color).
// solve: the rig's first frame on the sky (solved = plate-solved; estimated = mount pointing + rig size, pending solve).
window.SAMPLE_ROSTER = [
  { id: "justin", ini: "JB", name: "Justin", color: "#F2A541", filters: ["color"],
    rig: { name: "Backyard Newt", camera: "ZWO ASI2600MC Pro", telescope: "600 mm Newtonian (150 mm f/4)", px: [6248, 4176], pix: 3.76, efl: 600 },
    solve: { source: "solved", via: "ASIAIR plate solve", ra: 83.835, dec: -5.42, pa: 0.4 } },
  { id: "amy", ini: "AD", name: "Amy", color: "#4FD1C5", filters: ["color", "Ha"],
    rig: { name: "80 mm refractor", camera: "ZWO ASI533MC Pro", telescope: "80 mm f/5 refractor · Ha 7 nm clip-in for her Ha subs", px: [3008, 3008], pix: 3.76, efl: 400 },
    solve: { source: "solved", via: "astrometry.net (local)", ra: 83.74, dec: -5.17, pa: 37.0 } },
  { id: "bea", ini: "BA", name: "Bea", color: "#F472B6", filters: ["color"],
    rig: { name: "EdgeHD 8 + 0.7×", camera: "ZWO ASI294MC Pro", telescope: "Celestron EdgeHD 8 · 0.7× reducer", px: [4144, 2822], pix: 4.63, efl: 1422 },
    solve: { source: "estimated", via: "mount pointing + rig scale", ra: 83.86, dec: -5.36, pa: 0 },
    solved: { source: "solved", via: "astrometry.net (local)", ra: 83.83, dec: -5.40, pa: 352.5 } },
  { id: "cy", ini: "CY", name: "Cy", color: "#A3E635", filters: ["color"],
    rig: { name: "72ED + 585MC", camera: "ZWO ASI585MC Pro", telescope: "Sky-Watcher Evostar 72ED (420 mm)", px: [3840, 2160], pix: 2.9, efl: 420 },
    solve: { source: "solved", via: "ASIAIR plate solve", ra: 83.93, dec: -5.52, pa: 90.0 } },
  { id: "dana", ini: "DM", name: "Dana", tag: "Dana · OSC", color: "#A78BFA", filters: ["color"],
    rig: { name: "RedCat 71 (OSC)", camera: "ZWO ASI533MC Pro", telescope: "William Optics RedCat 71 (350 mm)", px: [3008, 3008], pix: 3.76, efl: 350 },
    solve: { source: "solved", via: "ASIAIR plate solve", ra: 83.70, dec: -5.47, pa: 12.0 } },
  { id: "dana2", ini: "DM", name: "Dana", tag: "Dana · 2nd rig", second: true, color: "#60A5FA", filters: ["L", "R", "G", "B"],
    rig: { name: "Esprit 100 mono", camera: "ZWO ASI1600MM Pro · LRGB filter wheel", telescope: "Sky-Watcher Esprit 100ED (550 mm)", px: [4656, 3520], pix: 3.8, efl: 550 },
    solve: { source: "solved", via: "ASIAIR plate solve", ra: 83.88, dec: -5.30, pa: 4.5 } },
  { id: "eli", ini: "EL", name: "Eli", color: "#F87171", filters: ["color", "Ha", "OIII"],
    rig: { name: "FRA400 + 183MC", camera: "ZWO ASI183MC Pro · dual-band filter for Ha / OIII", telescope: "Askar FRA400 (400 mm)", px: [5496, 3672], pix: 2.4, efl: 400 },
    solve: { source: "solved", via: "astrometry.net (local)", ra: 83.80, dec: -5.58, pa: 61.0 } },
];
// rig chips for a master tab, in roster order: "JB", "AD", ...
window.rosterRigs = (k) => window.SAMPLE_ROSTER.filter((r) => r.filters.includes(k)).map((r) => r.ini);
window.rosterRigTitles = (k) => window.SAMPLE_ROSTER.filter((r) => r.filters.includes(k)).map((r) => `${r.tag || r.name} · ${r.rig.name}`);
