# war.gov/UFO — Video Gallery + Downloader

Tools to pull the **videos** out of the U.S. Department of War UFO/UAP release
([war.gov/UFO](https://www.war.gov/ufo/), the "PURSUE" disclosure) so you can
review them and edit them together.

The official site mixes PDFs, images, audio, and video on one paginated page.
These tools isolate the **video** records, give you a single page to browse them,
and download every video file.

## What's here

| File | What it does |
|------|--------------|
| `gallery.html` | **Open this in a browser.** A searchable page showing every video record — title, agency, incident date/location, description. Click a card to play it (DVIDS embed), or use the link to open/download it on DVIDS. |
| `uap-records.csv` | Snapshot of the official catalog (Release 01: 161 records, 28 videos). `download_videos.py` refreshes this with the live catalog. |
| `build_gallery.py` | Regenerates `gallery.html` from the CSV. Pure Python, no installs. |
| `download_videos.py` | Downloads **every** video into `videos/`, then rebuilds the gallery to play/download your local copies. |
| `requirements.txt` | The one dependency (`playwright`) for the downloader. |

## Just want to browse the videos?

Open `gallery.html` in any browser. Nothing to install. Each card can play the
video inline (DVIDS player) and links to its DVIDS page, where there's usually a
download button.

> The committed page reflects **Release 01 (28 videos)**. The Pentagon adds files
> on a rolling basis, so run the downloader below to refresh to the latest release
> and grab all the actual video files.

## Download every video (for editing)

war.gov is behind Akamai bot protection — `curl`/`wget`/`requests` get blocked, so
the downloader drives a real browser.

```bash
cd ufo-video-gallery
pip install playwright
playwright install chromium
python3 download_videos.py
```

This will:
1. Refresh `uap-records.csv` from the live war.gov catalog (so you get every release).
2. Download each video to `videos/` (`.mp4`, named after its catalog title). Re-running skips files you already have.
3. Rebuild `gallery.html` so it plays and offers a **Download** button for each local file.

A Chromium window will open and drive itself — let it run.

## Rebuild the page only

If you edited the CSV or added files manually:

```bash
python3 build_gallery.py
```

## Compiling the videos

Once `videos/` is populated, stitch them with ffmpeg, e.g.:

```bash
# list every mp4, then concatenate (re-encode for safety across mixed formats)
for f in videos/*.mp4; do echo "file '$PWD/$f'"; done > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c:v libx264 -c:a aac compilation.mp4
```

## Notes

- These are public-domain U.S. Government records. The videos are hosted on DVIDS;
  this project only links to / embeds / downloads them.
- The war.gov modal + pagination handling in `download_videos.py` is adapted from
  the community downloader at <https://github.com/toor11/ufo>.
- If war.gov changes its page layout, the downloader's clicking logic may need a
  tweak; the gallery/CSV parsing will keep working regardless.
