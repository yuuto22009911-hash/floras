"""Generate docs/gallery.html with all bloom samples and their source inline."""

from __future__ import annotations

import html
from pathlib import Path

import floras

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
DOCS = ROOT / "docs"


ITEMS: list[dict[str, str]] = [
    {"name": "桜", "title": "桜", "subtitle": "5 弁 + 切れ込み"},
    {"name": "薔薇", "title": "薔薇", "subtitle": "28 弁螺旋 / 知覚色"},
    {"name": "菊", "title": "菊", "subtitle": "24 弁 / 細長い花弁"},
    {"name": "コスモス", "title": "コスモス", "subtitle": "茎 + 葉 4 枚"},
    {"name": "百合", "title": "百合", "subtitle": "色見本 連携"},
    {"name": "ヒーロー", "title": "ヒーロー", "subtitle": "1200×630 花束 (v0.3.0)"},
    {"name": "桜吹雪", "title": "桜吹雪", "subtitle": "散らす ─ 60 弁 (v0.4.0)"},
]


def build() -> None:
    cards: list[str] = []
    for item in ITEMS:
        bloom_path = EXAMPLES / f"{item['name']}.bloom"
        source = bloom_path.read_text(encoding="utf-8")
        svg = floras.render(source)
        wide = " wide" if item["name"] in {"ヒーロー", "桜吹雪"} else ""
        cards.append(
            f'  <figure class="card{wide}">\n'
            f'    <div class="preview{wide}">{svg}</div>\n'
            f'    <figcaption>'
            f'<strong>{html.escape(item["title"])}</strong>'
            f'<code>{item["name"]}.bloom — {html.escape(item["subtitle"])}</code>'
            f'</figcaption>\n'
            f'    <pre>{html.escape(source)}</pre>\n'
            f'  </figure>'
        )

    html_doc = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Floras Bloom — Gallery</title>
<style>
  :root {{
    color-scheme: light dark;
    --bg: #FAF7F2;
    --ink: #2C2825;
    --muted: #8A847C;
    --card: #FFFFFF;
    --border: rgba(44,40,37,0.08);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #15110D; --ink: #F4EFE6; --muted: #A39C90;
            --card: #1F1A14; --border: rgba(244,239,230,0.08); }}
  }}
  html, body {{ margin: 0; background: var(--bg); color: var(--ink); }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", system-ui, sans-serif;
    padding: clamp(24px, 5vw, 64px);
  }}
  header {{ margin-bottom: 48px; }}
  h1 {{ font-size: clamp(32px, 5vw, 56px); margin: 0 0 12px; letter-spacing: -0.02em; }}
  p.lead {{ color: var(--muted); margin: 0; max-width: 60ch; line-height: 1.6; }}
  main {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px; }}
  figure.wide {{ grid-column: 1 / -1; }}
  .preview.wide {{ aspect-ratio: 1200 / 630; max-width: 100%; }}
  .preview.wide svg {{ max-width: 100%; height: auto; }}
  figure {{
    margin: 0;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  }}
  .preview {{
    aspect-ratio: 1;
    display: grid;
    place-items: center;
    background:
      repeating-linear-gradient(45deg, transparent 0 8px, rgba(44,40,37,0.025) 8px 9px);
    border-radius: 8px;
    overflow: hidden;
  }}
  .preview svg {{ width: 100%; height: 100%; max-width: 320px; }}
  figcaption {{ display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }}
  figcaption strong {{ font-size: 18px; }}
  figcaption code {{ font-size: 12px; color: var(--muted); }}
  pre {{
    margin: 0;
    background: rgba(44,40,37,0.04);
    border-radius: 8px;
    padding: 12px 14px;
    font-size: 11px;
    line-height: 1.6;
    overflow-x: auto;
    font-family: ui-monospace, "SF Mono", Menlo, monospace;
    white-space: pre;
  }}
</style>
</head>
<body>
<header>
  <h1>Floras Bloom — Gallery</h1>
  <p class="lead">v0.1.0 で書ける単一 <code>bloom</code> の最小サンプル 5 種。すべて
  <code>floras render &lt;file&gt;.bloom</code> で生成された SVG。ソースは
  右上の <code>.bloom</code> 名で確認。</p>
</header>
<main>
{chr(10).join(cards)}
</main>
</body>
</html>
"""
    out = DOCS / "gallery.html"
    out.write_text(html_doc, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
