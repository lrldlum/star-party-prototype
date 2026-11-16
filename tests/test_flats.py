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
