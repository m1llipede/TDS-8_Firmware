#!/usr/bin/env python3
"""
Download every VIDEO from the war.gov/UFO (PURSUE) release.

war.gov sits behind Akamai bot protection that blocks curl/wget/requests, so the
only reliable way to fetch these files is from inside a real browser. This script
drives a real Chromium browser via Playwright:

  1. Opens war.gov/UFO/ and fetches the live catalog CSV (so you always get the
     newest release), saving it to uap-records.csv.
  2. Builds the list of VID records.
  3. For each video, opens its record modal and clicks the official download
     button, saving the .mp4 into ./videos/.  Already-downloaded files are skipped,
     so the script is safe to re-run.
  4. Rebuilds gallery.html so the page plays/links your local copies.

Setup (once):
    pip install playwright
    playwright install chromium

Run:
    python3 download_videos.py

Approach for the war.gov modal/pagination is adapted from the community
downloader at github.com/toor11/ufo.
"""
import asyncio
import csv
import io
import shutil
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    raise SystemExit(
        "Playwright is required.\n  pip install playwright\n  playwright install chromium"
    )

HERE = Path(__file__).resolve().parent
VIDEO_DIR = HERE / "videos"
CSV_PATH = HERE / "uap-records.csv"

BASE_URL = "https://www.war.gov"
CSV_URL = f"{BASE_URL}/Portals/1/Interactive/2026/UFO/uap-csv.csv"
RECORDS_PER_PAGE = 10  # war.gov lists records 10 per page, in CSV row order

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def safe_filename(title, ext=".mp4"):
    """Must match build_gallery.py so the gallery can find local files."""
    name = (title or "").strip().replace("/", "-").replace("\\", "-")
    return (name + ext) if name else ""


def parse_video_records(csv_text):
    csv_text = csv_text.lstrip("﻿")
    reader = csv.DictReader(io.StringIO(csv_text))
    records = []
    for i, raw in enumerate(reader, 1):
        row = {(k or "").strip(): (v or "").strip() for k, v in raw.items()}
        if row.get("Type", "").upper() != "VID":
            continue
        title = row.get("Title", "")
        dvids = row.get("DVIDS Video ID", "")
        fn = safe_filename(title) or (f"dvids-{dvids}.mp4" if dvids else None)
        if not fn:
            print(f"  [warn] row {i}: video with no title/DVIDS id, skipping")
            continue
        records.append({"row": i, "title": title, "dvids": dvids, "filename": fn})
    return records


async def get_page_num(page):
    active = page.locator(
        "#recordPagination button.is-active, #recordPagination a.is-active"
    )
    if await active.count() > 0:
        try:
            return int((await active.first.inner_text()).strip())
        except ValueError:
            pass
    return 1


async def nav_to_page(page, target):
    while await get_page_num(page) != target:
        btn = page.locator("#recordPagination button").filter(has_text=str(target))
        exact = None
        for j in range(await btn.count()):
            b = btn.nth(j)
            if (await b.inner_text()).strip() == str(target):
                exact = b
                break
        if exact and await exact.is_visible():
            await exact.click()
        else:
            await page.locator("#recordPagination button.pagination-next").click()
        await page.wait_for_load_state("networkidle", timeout=15000)
        await page.locator("button[data-record-trigger]").first.wait_for(
            state="visible", timeout=10000
        )


async def download_one(page, pos_on_page, dest, label):
    record_btn = page.locator("button[data-record-trigger]").nth(pos_on_page - 1)
    await record_btn.click()

    dl_btn = page.locator("button[data-record-modal-download]")
    await dl_btn.wait_for(state="visible", timeout=15000)
    for _ in range(30):  # wait until the button is enabled
        if await dl_btn.get_attribute("disabled") is None:
            break
        await page.wait_for_timeout(500)

    ok = False
    try:
        async with page.expect_download(timeout=600_000) as dl_info:
            await dl_btn.click()
        download = await dl_info.value
        if await download.failure():
            print(f"{label} download failed: {await download.failure()}")
        else:
            tmp = await download.path()
            if tmp:
                shutil.copy2(tmp, dest)
            else:
                await download.save_as(dest)
            print(f"{label} -> {dest.name} ({dest.stat().st_size/1e6:.1f} MB)")
            ok = True
    except Exception as e:
        print(f"{label} error: {e}")
    finally:
        try:
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(400)
            close = page.locator("button[data-record-modal-close]")
            if await close.count() > 0 and await close.is_visible():
                await close.click()
                await page.wait_for_timeout(300)
        except Exception:
            pass
    return ok


async def main():
    VIDEO_DIR.mkdir(exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-pdf-extension",
            ],
        )
        context = await browser.new_context(user_agent=USER_AGENT, accept_downloads=True)
        await context.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )
        page = await context.new_page()

        print("Loading war.gov/UFO/ ...")
        resp = await page.goto(f"{BASE_URL}/UFO/", wait_until="networkidle", timeout=60000)
        print(f"  status: {resp.status}")

        print("Fetching live catalog CSV ...")
        csv_text = await page.evaluate(
            "async (u) => (await fetch(u, {credentials:'include'})).text()", CSV_URL
        )
        CSV_PATH.write_text(csv_text, encoding="utf-8")
        records = parse_video_records(csv_text)
        print(f"  {len(records)} video records in catalog")

        # Group by war.gov list page (records render 10/page in CSV row order).
        by_page = {}
        for rec in records:
            pg = (rec["row"] - 1) // RECORDS_PER_PAGE + 1
            pos = (rec["row"] - 1) % RECORDS_PER_PAGE + 1
            by_page.setdefault(pg, []).append((pos, rec))

        ok = skip = fail = 0
        n = 0
        for pg in sorted(by_page):
            if await get_page_num(page) != pg:
                print(f"\nNavigating to list page {pg} ...")
                try:
                    await nav_to_page(page, pg)
                except Exception as e:
                    print(f"  [error] could not reach page {pg}: {e}")
                    fail += len(by_page[pg])
                    n += len(by_page[pg])
                    continue
            for pos, rec in by_page[pg]:
                n += 1
                dest = VIDEO_DIR / rec["filename"]
                label = f"[{n:>2}/{len(records)}] {rec['title'][:60]}"
                if dest.exists():
                    print(f"{label} [skip, already downloaded]")
                    skip += 1
                    continue
                print(f"\n{label}")
                if await download_one(page, pos, dest, label):
                    ok += 1
                else:
                    fail += 1
                await page.wait_for_timeout(1000)

        print(f"\nDone: {ok} downloaded | {skip} skipped | {fail} failed")
        await browser.close()

    # Rebuild the gallery so it uses the freshly downloaded files.
    try:
        import build_gallery
        build_gallery.main()
    except Exception as e:
        print(f"(Could not auto-rebuild gallery: {e}. Run: python3 build_gallery.py)")


if __name__ == "__main__":
    asyncio.run(main())
