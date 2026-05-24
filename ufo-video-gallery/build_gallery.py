#!/usr/bin/env python3
"""
Build gallery.html — a single self-contained page that highlights every VIDEO
record in the war.gov/UFO catalog.

Reads the catalog from uap-records.csv (a snapshot is committed; download_videos.py
refreshes it with the live catalog from war.gov). Filters to Type == VID and emits
a searchable card grid. Each card can play the DVIDS embed inline and links to the
DVIDS page (where the file can also be downloaded).

If videos have already been downloaded into ./videos/ (by download_videos.py), the
cards use a local <video> player and a direct "Download" link instead — ideal for
reviewing footage before editing.

No third-party dependencies. Run:  python3 build_gallery.py
"""
import csv
import datetime
import html
import io
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "uap-records.csv"
OUT_PATH = HERE / "gallery.html"
VIDEO_DIR = HERE / "videos"

DVIDS_VIDEO = "https://www.dvidshub.net/video/{id}"
DVIDS_EMBED = "https://www.dvidshub.net/video/embed/{id}"


def safe_filename(title, ext=".mp4"):
    """Filename used for a downloaded video. Must match download_videos.py."""
    name = (title or "").strip().replace("/", "-").replace("\\", "-")
    return (name + ext) if name else ""


def load_video_records(csv_path):
    text = csv_path.read_text(encoding="utf-8").lstrip("﻿")
    reader = csv.DictReader(io.StringIO(text))
    videos = []
    for i, raw in enumerate(reader, 1):
        row = {(k or "").strip(): (v or "").strip() for k, v in raw.items()}
        if row.get("Type", "").upper() != "VID":
            continue
        videos.append({
            "row": i,
            "title": row.get("Title", ""),
            "video_title": row.get("Video Title", ""),
            "dvids": row.get("DVIDS Video ID", ""),
            "agency": row.get("Agency", "") or "Unknown",
            "incident_date": row.get("Incident Date", ""),
            "incident_location": row.get("Incident Location", ""),
            "release_date": row.get("Release Date", ""),
            "description": row.get("Description Blurb", ""),
        })
    return videos


def card_html(v):
    e = html.escape
    fn = safe_filename(v["title"])
    local = "videos/" + fn if fn and (VIDEO_DIR / fn).exists() else ""
    dvids_page = DVIDS_VIDEO.format(id=v["dvids"]) if v["dvids"] else ""
    dvids_embed = DVIDS_EMBED.format(id=v["dvids"]) if v["dvids"] else ""

    title = v["video_title"] or v["title"]
    search_blob = " ".join([
        v["title"], v["video_title"], v["agency"],
        v["incident_location"], v["description"],
    ]).lower()

    meta_bits = []
    if v["incident_date"] and v["incident_date"].upper() != "N/A":
        meta_bits.append(f'<span class="chip">{e(v["incident_date"])}</span>')
    if v["incident_location"] and v["incident_location"].upper() != "N/A":
        meta_bits.append(f'<span class="chip">{e(v["incident_location"])}</span>')
    meta = "".join(meta_bits)

    links = []
    if local:
        links.append(f'<a class="btn primary" href="{e(local)}" download>Download</a>')
    if dvids_page:
        label = "DVIDS page" if local else "Watch / download on DVIDS"
        links.append(f'<a class="btn" href="{e(dvids_page)}" target="_blank" rel="noopener">{label}</a>')

    return f"""
    <article class="card" data-agency="{e(v['agency'])}" data-search="{e(search_blob)}">
      <div class="media" data-local="{e(local)}" data-embed="{e(dvids_embed)}">
        <button class="play" aria-label="Play video" {'disabled' if not (local or dvids_embed) else ''}>
          <span class="tri"></span>
        </button>
        <span class="badge">{e(v['agency'])}</span>
      </div>
      <div class="body">
        <h2>{e(title)}</h2>
        <div class="meta">{meta}</div>
        <p class="desc">{e(v['description'])}</p>
        <div class="links">{''.join(links)}
          <span class="dvids-id">DVIDS&nbsp;ID&nbsp;{e(v['dvids'])}</span>
        </div>
      </div>
    </article>"""


def build_html(videos):
    agencies = sorted({v["agency"] for v in videos})
    n_local = sum(1 for v in videos if safe_filename(v["title"]) and (VIDEO_DIR / safe_filename(v["title"])).exists())
    generated = datetime.date.today().isoformat()

    filter_buttons = '<button class="filt active" data-agency="">All</button>' + "".join(
        f'<button class="filt" data-agency="{html.escape(a)}">{html.escape(a)}</button>'
        for a in agencies
    )
    cards = "\n".join(card_html(v) for v in videos)

    local_note = (
        f'<strong>{n_local}</strong> of these are downloaded locally and play/download directly from this page.'
        if n_local else
        'No local copies yet &mdash; run <code>python3 download_videos.py</code> to fetch every video, '
        'then rebuild this page to play and download them here.'
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>war.gov/UFO &mdash; Videos</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
         background:#0b0e14; color:#e6e9ef; }}
  header {{ padding:28px 20px 18px; border-bottom:1px solid #1d2230;
           background:linear-gradient(180deg,#11151f,#0b0e14); position:sticky; top:0; z-index:5; }}
  h1 {{ margin:0 0 6px; font-size:24px; letter-spacing:.2px; }}
  .sub {{ color:#9aa3b2; font-size:14px; }}
  .sub code {{ background:#1a2030; padding:1px 6px; border-radius:5px; color:#cdd6f4; }}
  .controls {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-top:14px; }}
  #q {{ flex:1 1 240px; min-width:200px; padding:10px 12px; border-radius:9px; border:1px solid #2a3142;
        background:#121726; color:#e6e9ef; font-size:15px; }}
  .filters {{ display:flex; flex-wrap:wrap; gap:6px; }}
  .filt {{ background:#151b29; color:#aeb6c6; border:1px solid #2a3142; padding:7px 12px;
          border-radius:999px; cursor:pointer; font-size:13px; }}
  .filt.active {{ background:#2d6cdf; border-color:#2d6cdf; color:#fff; }}
  main {{ padding:20px; max-width:1300px; margin:0 auto; }}
  .grid {{ display:grid; gap:18px; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); }}
  .card {{ background:#121726; border:1px solid #1f2636; border-radius:14px; overflow:hidden;
          display:flex; flex-direction:column; }}
  .media {{ position:relative; aspect-ratio:16/9; background:
            radial-gradient(120% 120% at 50% 0%,#1c2438,#0c1019); display:flex;
            align-items:center; justify-content:center; cursor:pointer; }}
  .media iframe, .media video {{ width:100%; height:100%; border:0; display:block; background:#000; }}
  .play {{ width:64px; height:64px; border-radius:50%; border:2px solid #cdd6f4aa;
          background:#0c1019aa; cursor:pointer; display:grid; place-items:center; }}
  .play:disabled {{ opacity:.3; cursor:not-allowed; }}
  .tri {{ width:0; height:0; border-left:18px solid #e6e9ef; border-top:11px solid transparent;
         border-bottom:11px solid transparent; margin-left:5px; }}
  .badge {{ position:absolute; top:10px; left:10px; background:#0c1019cc; color:#aeb6c6;
           font-size:11px; letter-spacing:.5px; text-transform:uppercase; padding:4px 8px;
           border-radius:6px; border:1px solid #2a3142; }}
  .body {{ padding:14px 15px 16px; display:flex; flex-direction:column; gap:9px; flex:1; }}
  .body h2 {{ margin:0; font-size:16px; line-height:1.35; }}
  .meta {{ display:flex; flex-wrap:wrap; gap:6px; }}
  .chip {{ background:#1a2030; color:#9aa3b2; font-size:12px; padding:3px 8px; border-radius:6px; }}
  .desc {{ margin:0; color:#aeb6c6; font-size:13.5px; max-height:5.6em; overflow:hidden;
          position:relative; cursor:pointer; }}
  .desc.open {{ max-height:none; }}
  .desc:not(.open)::after {{ content:""; position:absolute; bottom:0; left:0; right:0; height:1.6em;
          background:linear-gradient(transparent,#121726); }}
  .links {{ margin-top:auto; display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
  .btn {{ background:#1a2233; color:#cdd6f4; border:1px solid #2a3142; padding:7px 12px;
         border-radius:8px; text-decoration:none; font-size:13px; }}
  .btn.primary {{ background:#2d6cdf; border-color:#2d6cdf; color:#fff; }}
  .btn:hover {{ filter:brightness(1.15); }}
  .dvids-id {{ color:#5d6678; font-size:11.5px; margin-left:auto; }}
  .empty {{ color:#9aa3b2; padding:40px; text-align:center; }}
  footer {{ color:#5d6678; font-size:12.5px; text-align:center; padding:26px 20px 40px; }}
  footer a {{ color:#7f8aa3; }}
</style>
</head>
<body>
<header>
  <h1>war.gov/UFO &mdash; Video Highlights</h1>
  <div class="sub">
    <strong>{len(videos)}</strong> video records &middot; source catalog:
    <code>war.gov/UFO</code> (PURSUE release) &middot; page built {generated}.<br>
    {local_note}
  </div>
  <div class="controls">
    <input id="q" type="search" placeholder="Search title, agency, location, description&hellip;">
    <div class="filters">{filter_buttons}</div>
  </div>
</header>
<main>
  <div class="grid" id="grid">
{cards}
  </div>
  <div class="empty" id="empty" hidden>No videos match your search.</div>
</main>
<footer>
  Public-domain U.S. Government records. Videos hosted on DVIDS; this page only links to / embeds them.<br>
  Rebuild with <code>python3 build_gallery.py</code> &middot; refresh catalog + download all with <code>python3 download_videos.py</code>.
</footer>
<script>
  // Click a card's media area to load its player (local file preferred, else DVIDS embed).
  document.querySelectorAll('.media').forEach(function(m) {{
    m.addEventListener('click', function() {{
      if (m.dataset.loaded) return;
      var local = m.dataset.local, embed = m.dataset.embed, el;
      if (local) {{
        el = document.createElement('video');
        el.controls = true; el.autoplay = true; el.src = local;
      }} else if (embed) {{
        el = document.createElement('iframe');
        el.src = embed; el.allow = 'autoplay; fullscreen; encrypted-media';
        el.setAttribute('allowfullscreen', '');
      }} else {{ return; }}
      m.innerHTML = ''; m.appendChild(el); m.dataset.loaded = '1'; m.style.cursor = 'default';
    }});
  }});
  // Expand/collapse long descriptions.
  document.querySelectorAll('.desc').forEach(function(d) {{
    d.addEventListener('click', function(e) {{ e.stopPropagation(); d.classList.toggle('open'); }});
  }});
  // Search + agency filter.
  var q = document.getElementById('q'), cards = [].slice.call(document.querySelectorAll('.card'));
  var agency = '';
  function apply() {{
    var term = q.value.trim().toLowerCase(); var shown = 0;
    cards.forEach(function(c) {{
      var ok = (!agency || c.dataset.agency === agency) &&
               (!term || c.dataset.search.indexOf(term) !== -1);
      c.hidden = !ok; if (ok) shown++;
    }});
    document.getElementById('empty').hidden = shown !== 0;
  }}
  q.addEventListener('input', apply);
  document.querySelectorAll('.filt').forEach(function(b) {{
    b.addEventListener('click', function() {{
      document.querySelectorAll('.filt').forEach(function(x) {{ x.classList.remove('active'); }});
      b.classList.add('active'); agency = b.dataset.agency; apply();
    }});
  }});
</script>
</body>
</html>"""


def main():
    if not CSV_PATH.exists():
        raise SystemExit(f"Catalog not found: {CSV_PATH}\nRun download_videos.py first, or restore uap-records.csv.")
    videos = load_video_records(CSV_PATH)
    OUT_PATH.write_text(build_html(videos), encoding="utf-8")
    n_local = sum(1 for v in videos if safe_filename(v["title"]) and (VIDEO_DIR / safe_filename(v["title"])).exists())
    print(f"Wrote {OUT_PATH.name}: {len(videos)} video records ({n_local} downloaded locally).")


if __name__ == "__main__":
    main()
