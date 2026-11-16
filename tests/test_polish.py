"""Polish-pass checks for the Star Party GitHub Pages prototype.

Run from the hosted folder (or this tests/ dir):

    python3 tests/test_polish.py
"""
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


def overflow_right(page, limit=431):
    return page.evaluate(
        """(limit) => [...document.querySelectorAll('body *')].filter(e => {
          if (!e.offsetParent || e.closest('svg') || e.closest('canvas') || e.closest('#strip') || e.closest('.cands') || e.closest('.sfade')) return false;
          const r = e.getBoundingClientRect();
          return r.right > limit + 1 && r.width > 0 && r.height > 0;
        }).map(e => e.id || e.className || e.tagName).slice(0, 8)""",
        limit,
    )


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

        # --- Master: send sheet is clearly a simulation; Escape closes ---
        page.goto(f"{base}/master.html#tab=Ha&sheet=Ha", wait_until="networkidle")
        page.wait_for_timeout(600)
        check("no pageerror on master", errors == [], errors)
        where = page.inner_text("#sendWhere")
        check("send copy says browser cannot write", "cannot write to an ASIAIR" in where and "native app" in where, where[:200])
        check("sheet is open", page.locator("#sheet").is_visible())
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        check("Escape closes download sheet", not page.locator("#sheet").is_visible())

        page.goto(f"{base}/master.html#tab=Ha&sheet=Ha&send=done", wait_until="networkidle")
        page.wait_for_timeout(400)
        res = page.inner_text("#sendRes")
        check("done state is labeled simulated", res.startswith("Simulated") and "nothing was written" in res.lower(), res[:200])

        check("390 master no overflow", overflow_right(page, 390) == [], overflow_right(page, 390))

        # --- Index hash stays in sync ---
        page.goto(f"{base}/index.html", wait_until="networkidle")
        page.wait_for_timeout(200)
        page.click("#next")
        page.wait_for_timeout(200)
        check("index Next writes #02_create_account", page.evaluate("location.hash") == "#02_create_account", page.evaluate("location.hash"))
        page.goto(f"{base}/index.html#15o_send_asiair", wait_until="networkidle")
        page.wait_for_timeout(800)
        title = page.inner_text("#title")
        check("index opens hash screen", "Send to ASIAIR" in title, title)

        # --- Sky: loading hides; hashchange to state=solved actually solves ---
        errors.clear()
        page.goto(f"{base}/sky.html#live=1", wait_until="networkidle")
        page.wait_for_timeout(800)
        check("no pageerror on sky", errors == [], errors)
        check("loading overlay hides after catalog loads", not page.locator("#mapMsg").is_visible())
        solved0 = page.inner_text("#cov")
        check("Bea still pending before timer / hash solve", "6 of 7" in solved0 or "SOLVED" in solved0, solved0)
        # The bug: setting hash to state=solved used to be ignored.
        page.evaluate("location.hash = 'state=solved'")
        page.wait_for_timeout(400)
        cov = page.inner_text("#cov")
        check("hash state=solved snaps Bea (7 of 7)", "7 of 7" in cov, cov)
        check("sky 390 no overflow", overflow_right(page, 390) == [], overflow_right(page, 390))

        # First paint of #state=solved must not be wiped by an early render/sync
        page.goto(f"{base}/sky.html#state=solved", wait_until="networkidle")
        page.wait_for_timeout(800)
        cov2 = page.inner_text("#cov")
        check("first load of #state=solved is 7 of 7", "7 of 7" in cov2, cov2)
        stars = page.evaluate("""() => {
          const cv = document.getElementById('cv');
          const ctx = cv.getContext('2d');
          const {width:w, height:h} = cv;
          const d = ctx.getImageData(0, 0, w, h).data;
          let bright = 0;
          for (let i = 0; i < d.length; i += 16) { if (d[i] > 180 && d[i+1] > 180 && d[i+2] > 180) bright++; }
          return {w, h, bright};
        }""")
        check("first load of sky draws the star catalog", stars["bright"] > 50, stars)

        # Sky error state
        page.route("**/sky/stars_m42.json", lambda route: route.abort())
        page.goto(f"{base}/sky.html", wait_until="networkidle")
        page.wait_for_timeout(400)
        msg = page.inner_text("#mapMsg")
        check("sky error state + retry", "Couldn't load the star map" in msg and page.locator("#retryStars").is_visible(), msg)
        page.unroute("**/sky/stars_m42.json")
        page.click("#retryStars")
        page.wait_for_timeout(800)
        check("sky retry recovers", not page.locator("#mapMsg").is_visible())

        # --- Rigs: Justin's gear presets, empty list, join doesn't crash, Escape closes delete ---
        errors.clear()
        page.goto(f"{base}/rigs.html#view=new&search=telescope&q=C6", wait_until="networkidle")
        page.wait_for_timeout(300)
        check("no pageerror on rigs", errors == [], errors)
        body = page.inner_text("#rTel")
        check("Celestron C6-A is a telescope preset", "Celestron C6-A" in body and "150 mm" in body and "1500 mm" in body, body[:300])

        page.goto(f"{base}/rigs.html#view=new&search=camera&q=2600MC%20Duo", wait_until="networkidle")
        page.wait_for_timeout(300)
        cam = page.inner_text("#rCam")
        check("ASI2600MC Pro Duo is a camera preset", "ZWO ASI2600MC Pro Duo" in cam, cam[:300])

        page.goto(f"{base}/rigs.html#view=list", wait_until="networkidle")
        page.wait_for_timeout(200)
        # delete all three rigs
        for _ in range(3):
            page.click("[data-del]")
            page.wait_for_timeout(100)
            check("delete dialog open", page.locator("#dlg").is_visible())
            page.keyboard.press("Escape")
            page.wait_for_timeout(100)
            # Escape should close without deleting the first time — only test once
            break
        check("Escape closes delete dialog", not page.locator("#dlg").is_visible())
        # actually delete all
        while page.locator("[data-del]").count():
            page.click("[data-del]")
            page.click("#dYes")
            page.wait_for_timeout(150)
        check("empty rigs state", page.locator("#emptyRigs").is_visible() and "No rigs yet" in page.inner_text("#emptyRigs"))

        page.goto(f"{base}/rigs.html#view=join")  # hash reload resets in-memory rigs, so join has sample rigs
        # To test empty join we must delete on the same page load
        page.goto(f"{base}/rigs.html#view=list", wait_until="networkidle")
        while page.locator("[data-del]").count():
            page.click("[data-del]")
            page.click("#dYes")
            page.wait_for_timeout(100)
        page.evaluate("go('join')")
        page.wait_for_timeout(150)
        join = page.inner_text("#join")
        check("empty join does not crash", "Add a rig first" in join, join[:200])
        check("empty join primary is enabled + Add a rig", page.locator("#jGo").is_enabled() and page.inner_text("#jGo").strip() == "+ Add a rig", page.inner_text("#jGo"))
        check("empty join drops the extra add-rig link", not page.locator("#jNew").is_visible())
        check("empty join does not repeat the scale sentence", join.lower().count("stacking and plate solving") == 1, join)

        # --- iPhone-sized viewports: fluid layout, no horizontal overflow ---
        for w, h, name in ((375, 667, "iPhone SE"), (393, 852, "iPhone 15"), (430, 932, "iPhone 16 Pro Max")):
            ip = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
            ip.goto(f"{base}/master.html#tab=color", wait_until="networkidle")
            ip.wait_for_timeout(500)
            ov = overflow_right(ip, w)
            check(f"{name} master no horizontal overflow", ov == [], ov)
            # shell fills the viewport
            ph = ip.evaluate("() => { const r=document.querySelector('.ph').getBoundingClientRect(); return {w:Math.round(r.width), h:Math.round(r.height)}; }")
            check(f"{name} master shell fills width", ph["w"] == min(w, 430), ph)
            ip.goto(f"{base}/sky.html#state=solved", wait_until="networkidle")
            ip.wait_for_timeout(600)
            ov = overflow_right(ip, w)
            check(f"{name} sky no horizontal overflow", ov == [], ov)
            ip.goto(f"{base}/rigs.html#view=list", wait_until="networkidle")
            ip.wait_for_timeout(300)
            ov = overflow_right(ip, w)
            check(f"{name} rigs no horizontal overflow", ov == [], ov)
            ip.close()

        # --- Send sheet on iPhone SE: sticky head/foot, backdrop, button on screen ---
        se = browser.new_page(viewport={"width": 375, "height": 667}, device_scale_factor=2)
        se.goto(f"{base}/master.html#tab=Ha&sheet=Ha", wait_until="networkidle")
        se.wait_for_timeout(500)
        geo = se.evaluate("""() => {
          const sh = document.getElementById('sheet');
          const head = document.querySelector('.sheet-head');
          const foot = document.querySelector('.sheet-foot');
          const btn = document.getElementById('sendBtn');
          const title = document.getElementById('shT');
          const x = document.getElementById('shX');
          const vis = (el) => { const r = el.getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight + 1 && r.height > 0; };
          return {
            sheetH: Math.round(sh.getBoundingClientRect().height),
            sheetTop: Math.round(sh.getBoundingClientRect().top),
            vh: innerHeight,
            headOn: vis(head) && vis(title) && vis(x),
            footOn: vis(foot) && vis(btn),
            btnText: btn.textContent,
          };
        }""")
        check("SE send sheet is shorter than the viewport (backdrop shows)", geo["sheetH"] < geo["vh"] and geo["sheetTop"] > 8, geo)
        check("SE send header (grab, title, close) stays on screen", geo["headOn"], geo)
        check("SE Send FITS button stays on screen", geo["footOn"], geo)

        se.goto(f"{base}/sky.html#state=solved", wait_until="networkidle")
        se.wait_for_timeout(700)
        sky = se.evaluate("""() => {
          const map = document.getElementById('map');
          const cv = document.getElementById('cv');
          const cov = document.getElementById('cov');
          const mr = map.getBoundingClientRect(), cr = cov.getBoundingClientRect();
          const tabs = document.querySelector('.tabs').getBoundingClientRect();
          return {
            mapW: Math.round(mr.width), mapH: Math.round(mr.height),
            canvasW: cv.width, cssW: Math.round(cv.getBoundingClientRect().width),
            dpr: window.devicePixelRatio,
            covBottom: Math.round(cr.bottom), tabsTop: Math.round(tabs.top),
            covVisible: cr.bottom <= tabs.top + 1 && cr.height > 0,
          };
        }""")
        check("SE sky map is fluid and shorter", sky["mapW"] <= 335 and sky["mapW"] >= 330 and sky["mapH"] <= 230, sky)
        check("SE sky canvas matches clientWidth * dpr", sky["canvasW"] == round(sky["cssW"] * sky["dpr"]), sky)
        check("SE sky coverage labels sit above the tab bar", sky["covVisible"], sky)
        se.close()

        # Safe-area: 83px at no inset; 68+34=102 with a 34px home indicator (not 83+34=117)
        page.goto(f"{base}/master.html#tab=color", wait_until="networkidle")
        page.wait_for_timeout(300)
        h0 = page.evaluate("() => Math.round(document.querySelector('.tabs').getBoundingClientRect().height)")
        check("tabs are 83px without a safe-area inset", h0 == 83, h0)
        insetH = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        insetH.goto(f"{base}/master.html#tab=color", wait_until="networkidle")
        insetH.add_style_tag(content=":root{--sat:47px;--sab:34px;--sal:0px;--sar:0px}")
        insetH.wait_for_timeout(200)
        h1 = insetH.evaluate("() => Math.round(document.querySelector('.tabs').getBoundingClientRect().height)")
        check("tabs are 102px with a 34px home-indicator inset", h1 == 102, h1)
        insetH.close()
        # Color Download/Share should stay above the tab bar with insets on a 393x852 frame
        inset = browser.new_page(viewport={"width": 393, "height": 852}, device_scale_factor=2)
        inset.goto(f"{base}/master.html#tab=color", wait_until="networkidle")
        inset.add_style_tag(content=":root{--sat:47px;--sab:34px;--sal:0px;--sar:0px}")
        inset.wait_for_timeout(500)
        btns = inset.evaluate("""() => {
          const row = document.querySelector('#chan .btns');
          const tabs = document.querySelector('.tabs');
          if (!row || !tabs) return {ok:false};
          const a = row.getBoundingClientRect(), b = tabs.getBoundingClientRect();
          return {ok: a.bottom <= b.top + 1, btnBottom: Math.round(a.bottom), tabsTop: Math.round(b.top), tabH: Math.round(b.height)};
        }""")
        check("iPhone 15 inset: Color Download/Share sit above the tab bar", btns["ok"], btns)
        inset.close()

        # Index walkthrough: hidden screenshot must not paint over the live iframe
        page.goto(f"{base}/index.html#15o_send_asiair", wait_until="networkidle")
        page.wait_for_timeout(800)
        img = page.evaluate("""() => {
          const el = document.getElementById('screen');
          const cs = getComputedStyle(el);
          return {hidden: el.hidden, display: cs.display, alt: el.alt, src: el.getAttribute('src')};
        }""")
        check("index live screen hides the walkthrough image", img["hidden"] and img["display"] == "none", img)
        check("index clears alt when the walkthrough image is hidden", img["alt"] == "", img)

        # PNG/JPEG size estimates appear on the download sheet
        page.goto(f"{base}/master.html#tab=Ha&sheet=Ha", wait_until="networkidle")
        page.wait_for_timeout(300)
        fmts = page.inner_text("#fmts")
        check("PNG and JPEG rows show a size estimate", "PNG" in fmts and "JPEG" in fmts and fmts.count("MB") >= 4, fmts[:400])

        # Bottom tabs are real links
        page.goto(f"{base}/master.html#tab=color", wait_until="networkidle")
        hrefs = page.evaluate("() => [...document.querySelectorAll('nav.tabs a')].map(a => a.getAttribute('href'))")
        check("bottom tabs are links", hrefs == ["master.html", "rigs.html", "rigs.html#view=list"], hrefs)

        browser.close()
    httpd.shutdown()
    print()
    if failed:
        print(f"{len(failed)} failed:")
        for f in failed:
            print(" -", f)
        raise SystemExit(1)
    print("All polish tests passed.")


if __name__ == "__main__":
    main()
