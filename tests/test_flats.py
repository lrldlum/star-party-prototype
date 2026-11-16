"""Flats-flow checks for the Star Party GitHub Pages prototype."""
from __future__ import annotations

import http.server
import socketserver
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/usr/bin/google-chrome"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def log_message(self, *a):
        pass


def start_server():
    httpd = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def main():
    httpd, base = start_server()
    failed = []

    def check(name, ok, detail=""):
        if ok:
            print(f"  PASS  {name}")
        else:
            print(f"  FAIL  {name}  {detail}")
            failed.append(f"{name}: {detail}")

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME)
        page = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # Default Color master must not show a flats badge (approved 390 frame).
        page.goto(f"{base}/master.html#tab=color", wait_until="networkidle")
        page.wait_for_timeout(500)
        check("no pageerror on master", errors == [], errors)
        check("default Color has no flats badge", not page.locator("#flatBadge").is_visible())
        check("default Color has no flats line", not page.locator("#flatLine").is_visible())
        check("Live stack is a link", (page.locator("#liveBack").get_attribute("href") or "").startswith("live.html"))

        # After / pending
        page.goto(f"{base}/master.html#tab=color&flats=after", wait_until="networkidle")
        page.wait_for_timeout(300)
        badge = page.inner_text("#flatBadge")
        check("after badge says uncalibrated, flats pending", "Uncalibrated, flats pending" in badge, badge)
        check("after preview is marked uncalibrated", "uncal" in (page.locator("#sky").get_attribute("class") or ""))
        check("honest copy is present on the flats line or page", "Add flats" in page.inner_text("#flatLine"), page.inner_text("body")[:200])

        page.goto(f"{base}/master.html#tab=color&flats=before", wait_until="networkidle")
        page.wait_for_timeout(200)
        badge = page.inner_text("#flatBadge")
        check("before badge says calibrated from frame 1", "Calibrated from frame 1" in badge, badge)
        check("before preview is not vignetted", "uncal" not in (page.locator("#sky").get_attribute("class") or ""))

        page.goto(f"{base}/master.html#tab=color&flats=library&lib=nov8", wait_until="networkidle")
        page.wait_for_timeout(200)
        badge = page.inner_text("#flatBadge")
        check("library badge shows the set date", "library flats" in badge.lower() and "Nov 8" in badge, badge)

        page.goto(f"{base}/master.html#tab=color&flats=after&restack=done", wait_until="networkidle")
        page.wait_for_timeout(200)
        badge = page.inner_text("#flatBadge")
        check("restack-done badge is calibrated", "Calibrated" in badge and "pending" not in badge.lower(), badge)

        # Party menu opens Flats and closes on Escape
        page.goto(f"{base}/master.html#tab=color", wait_until="networkidle")
        page.click("#menuBtn")
        page.wait_for_timeout(150)
        check("party menu opens", page.locator("#menu").is_visible())
        check("party menu has Flats", "Flats" in page.inner_text("#menu"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(150)
        check("Escape closes party menu", not page.locator("#menu").is_visible())

        # Flats settings: three methods, warning, library date, add+restack
        errors.clear()
        page.goto(f"{base}/flats.html#view=session&flats=after", wait_until="networkidle")
        page.wait_for_timeout(300)
        check("no pageerror on flats", errors == [], errors)
        body = page.inner_text("#panel")
        check("all three methods are listed", "Flats before the session" in body and "Flat library" in body and "Flats after (traditional)" in body, body[:400])
        check("honest prototype copy", "native app applies" in body.lower() and "calibrated FITS" in body, body[-400:])
        check("after state has Add flats and re-stack", page.locator("#addFlats").is_visible())

        page.goto(f"{base}/flats.html#view=session&flats=before", wait_until="networkidle")
        page.wait_for_timeout(200)
        warn = page.inner_text("#flatWarn")
        check("before warns about focus, rotation and camera", "focus" in warn.lower() and "rotation" in warn.lower() and "camera" in warn.lower(), warn)

        page.goto(f"{base}/flats.html#view=session&flats=library&lib=nov8", wait_until="networkidle")
        page.wait_for_timeout(200)
        box = page.inner_text("#libApplied")
        check("library shows applied set and date", "Nov 8, 2026" in box and "600 mm" in box, box)

        page.goto(f"{base}/flats.html#view=library&flats=library&lib=nov8", wait_until="networkidle")
        page.wait_for_timeout(200)
        lib = page.inner_text("#panel")
        check("library picker lists Nov 8 and Oct 19", "Nov 8, 2026" in lib and "Oct 19, 2026" in lib, lib[:400])

        page.goto(f"{base}/flats.html#view=rigs", wait_until="networkidle")
        page.wait_for_timeout(200)
        rigs = page.inner_text("#panel")
        check("each-rig list includes Dana's two methods", "Dana · OSC" in rigs and "Dana · 2nd rig" in rigs, rigs[:500])
        check("Eli is pending flats", "Eli" in rigs and "pending" in rigs.lower(), rigs)

        page.goto(f"{base}/flats.html#view=restack&flats=after&restack=progress", wait_until="networkidle")
        page.wait_for_timeout(200)
        check("restack progress is visible", page.locator("#bar").is_visible() and "Re-stacking" in page.inner_text("#panel"))

        page.goto(f"{base}/flats.html#view=restack&flats=after&restack=done", wait_until="networkidle")
        page.wait_for_timeout(200)
        check("restack done has before/after compare", page.locator("#cmpF").is_visible() and "Uncalibrated" in page.inner_text("#panel") and "Calibrated" in page.inner_text("#panel"))

        # Live stack badges
        errors.clear()
        page.goto(f"{base}/live.html#flats=after", wait_until="networkidle")
        page.wait_for_timeout(300)
        check("no pageerror on live", errors == [], errors)
        check("live after badge", "Uncalibrated, flats pending" in page.inner_text("#flatBadge"), page.inner_text("body")[:300])
        check("live after has Add flats", "Add flats" in page.inner_text("#panel"))

        page.goto(f"{base}/live.html#flats=before", wait_until="networkidle")
        page.wait_for_timeout(200)
        check("live before badge", "Calibrated from frame 1" in page.inner_text("#flatBadge"))

        page.goto(f"{base}/live.html#flats=library&lib=nov8", wait_until="networkidle")
        page.wait_for_timeout(200)
        check("live library badge includes Nov 8", "Nov 8" in page.inner_text("#flatBadge"))

        page.goto(f"{base}/live.html#flats=after&restack=progress", wait_until="networkidle")
        page.wait_for_timeout(200)
        check("live re-stack progress", page.locator("#bar").is_visible() and "Re-stacking" in page.inner_text("#panel"))

        page.goto(f"{base}/live.html#flats=after&restack=done", wait_until="networkidle")
        page.wait_for_timeout(200)
        check("live re-stack compare", page.locator("#cmpF").is_visible())
        check("live compare before layer is vignetted", page.locator("#cmpF .vignette-wrap").count() == 1)
        check("live compare calibrated image is outside the vignette", page.locator("#cmpF > img").count() == 1)
        check("live compare does not sit Calibrated mid-paragraph", "Calibrated" not in (page.locator(".status").inner_text() if page.locator(".status").count() else ""))

        page.goto(f"{base}/flats.html#view=restack&flats=after&restack=done", wait_until="networkidle")
        page.wait_for_timeout(200)
        check("flats compare before layer is vignetted", page.locator("#cmpF .vignette-wrap").count() == 1)
        vg = page.evaluate("""() => {
          const el = document.querySelector('#cmpF .vignette-wrap');
          const bg = el ? getComputedStyle(el, '::after').backgroundImage : '';
          return {ok: bg.includes('radial-gradient'), bg};
        }""")
        check("flats compare uses the uncal radial vignette", vg["ok"], vg)

        # Binning is part of library matching (camera, filter, bin).
        page.goto(f"{base}/flats.html#view=library&flats=library&lib=nov8", wait_until="networkidle")
        page.wait_for_timeout(200)
        lib = page.inner_text("#panel")
        check("library header includes bin 1×1", "bin 1×1" in lib or "bin 1x1" in lib.lower(), lib[:400])
        check("library cards include bin", "bin 1×1" in lib, lib)
        check("2×2 set is excluded by the bin matcher", "Jul 22" not in lib, lib)
        match = page.evaluate("""() => {
          const hits = FLATS.matchLib(FLATS.SESSION_MATCH).map((l) => l.id + ':' + l.bin);
          const x2 = FLATS.matchLib(Object.assign({}, FLATS.SESSION_MATCH, {bin: '2×2'})).map((l) => l.id);
          const line = FLATS.libLine(FLATS.libById('nov8'));
          return {hits, x2, line};
        }""")
        check("matchLib at bin 1×1 returns nov8 and oct19 only", match["hits"] == ["nov8:1×1", "oct19:1×1"], match)
        check("matchLib at bin 2×2 returns jul22 only", match["x2"] == ["jul22"], match)
        check("libLine includes bin", "bin 1×1" in match["line"], match["line"])

        # Per-rig editor binds to that rig, not the session method.
        page.goto(f"{base}/flats.html#view=rigs&who=dana2&flats=library&lib=nov8", wait_until="networkidle")
        page.wait_for_timeout(200)
        rig = page.evaluate("""() => {
          const on = [...document.querySelectorAll('[data-mode]')].filter((b) => b.getAttribute('aria-checked') === 'true').map((b) => b.dataset.mode);
          return {on, hasAdd: !!document.getElementById('addFlats'), hash: location.hash, title: document.querySelector('h1') && document.querySelector('h1').innerText};
        }""")
        check("Dana 2nd rig opens on its own after method, not session library", rig["on"] == ["after"] and rig["hasAdd"], rig)
        check("opening a rig does not overwrite the session flats hash", "flats=library" in rig["hash"], rig)
        page.click("[data-mode='before']")
        page.wait_for_timeout(200)
        after_pick = page.evaluate("""() => {
          const on = [...document.querySelectorAll('[data-mode]')].filter((b) => b.getAttribute('aria-checked') === 'true').map((b) => b.dataset.mode);
          const warn = (document.getElementById('flatWarn') || {}).innerText || '';
          return {on, warn, hash: location.hash, saved: FLATS.getRig('dana2').mode};
        }""")
        check("picking before on Dana 2nd rig selects before", after_pick["on"] == ["before"], after_pick)
        check("per-rig before shows the optical-train warning", "focus" in after_pick["warn"].lower() and "rotation" in after_pick["warn"].lower(), after_pick)
        check("picking a rig method does not rewrite the session hash", "flats=library" in after_pick["hash"] and "flats=before" not in after_pick["hash"], after_pick)
        check("the pick is saved on that rig", after_pick["saved"] == "before", after_pick)
        page.click("#back")
        page.wait_for_timeout(200)
        # back from one-rig editor goes to session; open the list
        if "view=rigs" not in (page.evaluate("location.hash") or ""):
            if page.locator("#seeRigs").count():
                page.click("#seeRigs")
                page.wait_for_timeout(200)
        list_txt = page.inner_text("#panel")
        check("rig list updates Dana 2nd rig after the pick", "Dana · 2nd rig" in list_txt and "From frame 1" in list_txt, list_txt)
        check("Cy's session-flats line uses Cy's name, not her", "before Cy's first sub" in list_txt and "before her first sub" not in list_txt, list_txt)

        # Optional polish: catalog error sits outside the map, not over Cy/Bea labels
        page.route("**/sky/stars_m42.json", lambda route: route.abort())
        page.goto(f"{base}/sky.html#state=solved", wait_until="networkidle")
        page.wait_for_timeout(400)
        geo = page.evaluate("""() => {
          const map = document.getElementById('map').getBoundingClientRect();
          const msg = document.getElementById('mapMsg').getBoundingClientRect();
          const mid = {x: map.left + map.width/2, y: map.top + map.height/2};
          const coversCenter = msg.left < mid.x && mid.x < msg.right && msg.top < mid.y && mid.y < msg.bottom && msg.height > 40;
          return {coversCenter, msgTop: Math.round(msg.top), mapBottom: Math.round(map.bottom), msgText: document.getElementById('mapMsg').innerText};
        }""")
        check("sky error copy is present", "Couldn't load the star map" in geo["msgText"], geo)
        check("sky error message does not cover the map center (Cy/Bea)", not geo["coversCenter"] and geo["msgTop"] >= geo["mapBottom"] - 1, geo)
        page.unroute("**/sky/stars_m42.json")

        def geometry(pg, cta_sel):
            return pg.evaluate("""(sel) => {
              const tabs = document.querySelector('.tabs');
              const cta = document.querySelector(sel);
              const warn = document.getElementById('flatWarn') || document.getElementById('libApplied');
              const fade = document.querySelector('.sfade:not(.off) span');
              const tb = tabs.getBoundingClientRect();
              const r = cta ? cta.getBoundingClientRect() : null;
              const w = warn ? warn.getBoundingClientRect() : null;
              const f = fade ? fade.getBoundingClientRect() : null;
              return {
                tabsTop: Math.round(tb.top),
                ctaTop: r ? Math.round(r.top) : null,
                ctaBottom: r ? Math.round(r.bottom) : null,
                warnTop: w ? Math.round(w.top) : null,
                warnBottom: w ? Math.round(w.bottom) : null,
                gap: r ? Math.round(tb.top - r.bottom) : null,
                warnGap: w ? Math.round(tb.top - w.bottom) : null,
                fadeTop: f ? Math.round(f.top) : null,
                fadeOverlapsCta: !!(r && f && f.top < r.bottom - 1 && f.bottom > r.top + 1 && f.left < r.right && f.right > r.left),
                ctaText: cta ? cta.innerText.trim() : null,
              };
            }""", cta_sel)

        # 59px top inset: Download/Share sit above the tab bar with a few px gap
        inset = browser.new_page(viewport={"width": 393, "height": 852}, device_scale_factor=2)
        inset.goto(f"{base}/master.html#tab=color", wait_until="networkidle")
        inset.add_style_tag(content=":root{--sat:59px!important;--sab:34px!important;--sal:0px!important;--sar:0px!important}")
        inset.wait_for_timeout(400)
        gap = inset.evaluate("""() => {
          const row = document.querySelector('#chan .btns');
          const tabs = document.querySelector('.tabs');
          const a = row.getBoundingClientRect(), b = tabs.getBoundingClientRect();
          return {gap: Math.round(b.top - a.bottom), tabH: Math.round(b.height), btnBottom: Math.round(a.bottom), tabsTop: Math.round(b.top)};
        }""")
        check("59px top inset: Download/Share stay above the tab bar", gap["gap"] >= 0, gap)
        check("59px top inset: a few px of gap above the tab bar", gap["gap"] >= 8, gap)

        inset.goto(f"{base}/master.html#tab=color&flats=after", wait_until="networkidle")
        inset.add_style_tag(content=":root{--sat:59px!important;--sab:34px!important;--sal:0px!important;--sar:0px!important}")
        inset.wait_for_timeout(400)
        gap2 = inset.evaluate("""() => {
          const row = document.querySelector('#chan .btns');
          const tabs = document.querySelector('.tabs');
          const a = row.getBoundingClientRect(), b = tabs.getBoundingClientRect();
          return {gap: Math.round(b.top - a.bottom), btnBottom: Math.round(a.bottom), tabsTop: Math.round(b.top), hasFlats: document.body.classList.contains('has-flats')};
        }""")
        check("59px inset Color with flats line: Download/Share above the tab bar", gap2["gap"] >= 0, gap2)
        check("59px inset Color with flats line: at least 8px gap", gap2["gap"] >= 8, gap2)

        # Session confirmation + CTA stay in the first viewport (375 and 393+59/34)
        def check_fold(pg, label, url, cta_sel):
            pg.goto(f"{base}/{url}", wait_until="networkidle")
            if "393" in label:
                pg.add_style_tag(content=":root{--sat:59px!important;--sab:34px!important;--sal:0px!important;--sar:0px!important}")
            pg.wait_for_timeout(300)
            geo = geometry(pg, cta_sel)
            check(f"{label}: confirmation is in the first viewport", geo["warnTop"] is not None and geo["warnBottom"] <= geo["tabsTop"] - 4, geo)
            check(f"{label}: CTA is in the first viewport with a gap above the tab bar", geo["ctaBottom"] is not None and geo["gap"] >= 8, geo)
            if "375 after" in label:
                check(f"{label}: More below does not sit on the CTA", not geo["fadeOverlapsCta"], geo)
            return geo

        se = browser.new_page(viewport={"width": 375, "height": 667}, device_scale_factor=2)
        check_fold(se, "375 after", "flats.html#view=session&flats=after", "#addFlats")
        check_fold(se, "375 before", "flats.html#view=session&flats=before", "#flatWarn")
        check_fold(se, "375 library", "flats.html#view=session&flats=library&lib=nov8", "#browse")
        # F05: Dana 2nd and Eli above the fold on 390 (and try 375)
        se.close()
        list390 = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        list390.goto(f"{base}/flats.html#view=rigs", wait_until="networkidle")
        list390.wait_for_timeout(300)
        fit = list390.evaluate("""() => {
          const tabs = document.querySelector('.tabs').getBoundingClientRect();
          const names = [...document.querySelectorAll('[data-who]')].map((b) => {
            const r = b.getBoundingClientRect();
            return {id: b.dataset.who, name: b.querySelector('b').innerText, bottom: Math.round(r.bottom), top: Math.round(r.top)};
          });
          const dana2 = names.find((n) => n.id === 'dana2');
          const eli = names.find((n) => n.id === 'eli');
          return {tabsTop: Math.round(tabs.top), dana2, eli, names};
        }""")
        check("F05 Dana 2nd rig is above the fold", fit["dana2"] and fit["dana2"]["bottom"] <= fit["tabsTop"] - 4, fit)
        check("F05 Eli is above the fold", fit["eli"] and fit["eli"]["bottom"] <= fit["tabsTop"] - 4, fit)
        list390.close()

        check_fold(inset, "393insets after", "flats.html#view=session&flats=after", "#addFlats")
        check_fold(inset, "393insets before", "flats.html#view=session&flats=before", "#flatWarn")
        check_fold(inset, "393insets library", "flats.html#view=session&flats=library&lib=nov8", "#browse")
        inset.close()

        browser.close()
    httpd.shutdown()
    print()
    if failed:
        print(f"{len(failed)} failed:")
        for f in failed:
            print(" -", f)
        raise SystemExit(1)
    print("All flats tests passed.")


if __name__ == "__main__":
    main()
