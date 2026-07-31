"""Self-contained HTML gallery generator for Hermes Image Studio.

Reads generation history from SQLite and produces a single HTML file
that renders a browsable gallery of every generated image. The HTML
references local image files via relative paths, so it works by opening
the file in any browser (no server needed).
"""

from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from image_studio import history

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PRESET_COLORS = {
    "cinematic": "#e74c3c",
    "photorealistic": "#2ecc71",
    "vintage": "#f39c12",
    "fantasy": "#9b59b6",
    "minimalist": "#95a5a6",
    "illustration": "#3498db",
    "noir": "#34495e",
    "studio": "#1abc9c",
    "gpt-photo": "#e67e22",
    "gpt-art": "#c0392b",
    "banana-photo": "#16a085",
    "edit": "#7f8c8d",
}


def _esc(text: Any) -> str:
    """Escape text for safe embedding in HTML."""
    return html.escape(str(text if text is not None else ""))


def _short_prompt(prompt: str, limit: int = 80) -> str:
    prompt = prompt.strip()
    if len(prompt) <= limit:
        return prompt
    return prompt[: limit - 3].rstrip() + "..."


def _relative_path(file_path: str) -> str:
    """Return a browser-friendly relative path from the gallery file's dir."""
    return file_path.replace("\\", "/")


def _format_time(created_at: str) -> str:
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return created_at


def _preset_color(preset: Optional[str]) -> str:
    return _PRESET_COLORS.get(preset or "", "#7f8c8d")


# ---------------------------------------------------------------------------
# Gallery generation
# ---------------------------------------------------------------------------


def build_gallery(
    output_path: Optional[str] = None,
    *,
    limit: int = 0,
) -> str:
    """Generate a self-contained HTML gallery of all generations.

    Args:
        output_path: Where to write the HTML file. Defaults to
            'gallery.html' next to the history DB.
        limit: Max entries to include (0 = all).

    Returns:
        Absolute path to the written HTML file.
    """
    entries = history.recent_generations(limit if limit > 0 else 10000)
    # Show oldest first in the gallery for a natural reading order
    entries = list(reversed(entries))

    total_cost = history.total_cost()
    total_count = history.count_generations()

    cards = []
    for e in entries:
        file_path = e.get("file_path", "")
        if not file_path or not os.path.isfile(file_path):
            continue
        img_src = _relative_path(file_path)
        preset = e.get("preset") or ""
        color = _preset_color(preset)
        model = e.get("model") or ""
        seed = e.get("seed", "")
        aspect = e.get("aspect_ratio") or ""
        width = e.get("width") or ""
        height = e.get("height") or ""
        cost = float(e.get("cost_usd") or 0.0)
        created = _format_time(e.get("created_at", ""))

        dims = f"{width}x{height}" if width and height else aspect

        cards.append(f"""
        <figure class="card" data-preset="{_esc(preset)}" data-model="{_esc(model)}">
          <a href="{_esc(img_src)}" target="_blank">
            <img src="{_esc(img_src)}" alt="{_esc(_short_prompt(e.get('prompt', ''), 60))}" loading="lazy">
          </a>
          <figcaption>
            <div class="meta">
              <span class="badge" style="background:{color}">{_esc(preset or 'unknown')}</span>
              <span class="model">{_esc(model)}</span>
              <span class="dims">{_esc(dims)}</span>
            </div>
            <div class="prompt" title="{_esc(e.get('prompt', ''))}">{_esc(_short_prompt(e.get('prompt', '')))}</div>
            <div class="sub">
              <span>seed {_esc(seed)}</span>
              <span>{_esc(created)}</span>
              <span>${cost:.3f}</span>
            </div>
          </figcaption>
        </figure>""")

    # Distinct presets and models for filter chips
    preset_keys = []
    for e in entries:
        p = e.get("preset") or ""
        if p and p not in preset_keys:
            preset_keys.append(p)
    model_keys = []
    for e in entries:
        m = e.get("model") or ""
        if m and m not in model_keys:
            model_keys.append(m)

    preset_chips = "\n".join(
        f'<button class="chip" data-filter="{_esc(p)}" style="--c:{_preset_color(p)}">{_esc(p)}</button>'
        for p in sorted(preset_keys)
    )
    model_chips = "\n".join(
        f'<button class="chip chip-model" data-filter="{_esc(m)}">{_esc(m)}</button>'
        for m in sorted(model_keys)
    )

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hermes Image Studio Gallery</title>
<style>
  :root {{ --bg:#0f1115; --panel:#171a21; --text:#e8eaed; --muted:#9aa0a6;
          --border:#2a2f3a; --accent:#7c5cff; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          background:var(--bg); color:var(--text); }}
  header {{ position:sticky; top:0; z-index:10; background:rgba(15,17,21,.92);
           backdrop-filter:blur(8px); border-bottom:1px solid var(--border); padding:18px 28px; }}
  h1 {{ margin:0 0 4px; font-size:20px; font-weight:700; }}
  .stats {{ color:var(--muted); font-size:13px; margin:0; }}
  .filters {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }}
  .chip {{ background:var(--panel); color:var(--muted); border:1px solid var(--border);
          border-radius:999px; padding:5px 14px; font-size:12px; cursor:pointer; }}
  .chip:hover, .chip.active {{ color:#fff; border-color:var(--accent); }}
  .chip-model:hover, .chip-model.active {{ color:#fff; border-color:#2ecc71; }}
  main {{ padding:28px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr));
          gap:20px; }}
  .card {{ margin:0; background:var(--panel); border:1px solid var(--border);
          border-radius:12px; overflow:hidden; transition:transform .15s, border-color .15s; }}
  .card:hover {{ transform:translateY(-2px); border-color:var(--accent); }}
  .card.hidden {{ display:none; }}
  .card img {{ width:100%; aspect-ratio:16/10; object-fit:cover; display:block; }}
  figcaption {{ padding:12px 14px 14px; }}
  .meta {{ display:flex; align-items:center; gap:8px; margin-bottom:8px; }}
  .badge {{ color:#fff; font-size:11px; font-weight:600; padding:2px 9px; border-radius:999px; }}
  .model {{ color:var(--muted); font-size:12px; }}
  .dims {{ margin-left:auto; color:var(--muted); font-size:12px; }}
  .prompt {{ font-size:13px; line-height:1.45; margin:0 0 8px; color:var(--text); }}
  .sub {{ display:flex; gap:14px; color:var(--muted); font-size:12px; }}
  .empty {{ color:var(--muted); text-align:center; padding:80px 20px; }}
  footer {{ color:var(--muted); font-size:12px; padding:20px 28px 40px; text-align:center; }}
</style>
</head>
<body>
<header>
  <h1>🖼️ Hermes Image Studio</h1>
  <p class="stats">{total_count} generations · ${total_cost:.2f} total spend</p>
  <div class="filters">
    <button class="chip active" data-filter="all">All</button>
    {preset_chips}
    {model_chips}
  </div>
</header>
<main>
  <div class="grid" id="grid">
    {''.join(cards) if cards else '<p class="empty">No generated images yet. Generate one with image_studio_generate and rebuild this gallery.</p>'}
  </div>
</main>
<footer>Generated by Hermes Image Studio · {_esc(datetime.now().strftime('%Y-%m-%d %H:%M'))}</footer>
<script>
  const grid = document.getElementById('grid');
  const chips = document.querySelectorAll('.chip');
  chips.forEach(chip => {{
    chip.addEventListener('click', () => {{
      chips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const f = chip.dataset.filter;
      grid.querySelectorAll('.card').forEach(card => {{
        const preset = card.dataset.preset || '';
        const model = card.dataset.model || '';
        card.classList.toggle('hidden', f !== 'all' && preset !== f && model !== f);
      }});
    }});
  }});
</script>
</body>
</html>"""

    if not output_path:
        db_dir = os.path.dirname(os.path.abspath(history._db_path()))
        output_path = os.path.join(db_dir, "gallery.html")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

    return os.path.abspath(output_path)
