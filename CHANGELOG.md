# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-07

### Added — Web プレイグラウンド (Pyodide)
- New `playground/` directory with a single-file HTML playground that
  runs Floras Bloom entirely in the browser via Pyodide. No backend, no
  build step (vanilla HTML + CSS + JS).
- Features:
  - Editable `<textarea>` with the source on the left, live SVG preview
    on the right.
  - 6 built-in samples (さくら / ばら / こすもす / ヒーロー / 桜吹雪 / 枝).
    Switching samples auto-renders.
  - 描画 button + `⌘↩` / `Ctrl↩` shortcut.
  - 共有 button base64-encodes the source into the URL hash. Loading the
    URL on another machine restores the source automatically.
  - Status badge in the header shows Pyodide load progress and turns into
    "● live" when ready.
  - Dark / light mode follows `prefers-color-scheme`.
- `playground/build.sh` rebuilds the wheel and patches the version
  reference in `index.html` after every version bump.
- `playground/floras-1.0.0-py3-none-any.whl` is shipped alongside the
  HTML so the playground works on any static host (Cloudflare Pages,
  GitHub Pages, S3) — drop the directory and serve.

### Changed
- Package classifier upgraded to `Development Status :: 5 - Production/Stable`.
- Version bumped from 0.7.0 → 1.0.0; the wheel is regenerated to match.

### Quality gates
- pytest 97 / 97 pass, ruff strict / mypy strict 0 errors.
- Playground verified end-to-end: Pyodide boots in ~5–10 s on a fresh
  load, then `さくら`, `桜吹雪` (60 scatter), and `枝 (模様)` all render
  correctly inside the browser.

## [0.7.0] - 2026-05-07

### Added — `floras tokens` (palette export to CSS / Tailwind / JSON)
- New CLI subcommand `floras tokens <file>.bloom [--out <path>] [--format css|tailwind|json]`.
- Three output formats:
  - **css** (default): `:root { --<palette>-<token>: #RRGGBB; ... }`. Modern
    browsers accept non-ASCII identifiers in CSS custom properties, so
    variable names land as `--春-桜色` directly.
  - **tailwind**: `@theme { --color-<palette>-<token>: #RRGGBB; ... }` —
    drops straight into a Tailwind v4 `app.css`.
  - **json**: nested `{ "<palette>": { "<token>": "#RRGGBB" } }` for
    consumption by build pipelines (TS / design tokens / Style Dictionary).
- 10 new tests cover the three renderers, empty palettes, determinism,
  CLI stdout / file output for all three formats, missing file (exit 2),
  and syntax error in source (exit 1). All 97 tests pass; ruff and mypy
  strict still green.

## [0.6.0] - 2026-05-07

### Added — `floras preview` (live reload)
- New CLI subcommand `floras preview <directory> [--port N]` (defaults to
  port 7878) that:
  - Serves an HTML gallery of every `.bloom` in `<directory>` with each SVG
    rendered inline.
  - Watches the directory by polling mtimes (default: 1.0 s) and pushes a
    Server-Sent Event whenever a file is added, modified, or removed.
  - The browser swaps just the affected `<svg>` without a full reload (~1 s
    end-to-end). A "live" indicator in the bottom-right shows the SSE state.
  - If a `.bloom` has a syntax / validation error, the matching card switches
    to a red "error" panel showing the message — the server itself never
    crashes, and recovers as soon as the file becomes valid again.
  - Falls back to the next free port if `--port` is taken (tries
    `port .. port+10`); accepts `--port 0` to ask the OS for any port
    (used by tests).
- Implementation is pure Python standard library (`http.server`,
  `threading`, `queue`); no new runtime dependency.
- 7 new tests cover gallery HTML / SVG endpoint / unknown file fallback /
  SSE change events / syntax-error rendering / missing directory / port
  collision. All 87 tests pass; ruff and mypy strict still green.

## [0.5.0] - 2026-05-07

### Added — 模様 (motif)
- New top-level declaration `模様 名前 { 置く ... に (x, y); ... }`. A motif
  is a reusable group of placements with local coordinates (origin = 0, 0).
- A motif can be placed in a 花束 with `置く 模様名 に (x, y)` or `置く 模様名 に
  中央`. Each child placement is translated to (x, y).
- `散らす` accepts a motif as `元`; every generated position spawns a full
  copy of the motif.
- A motif may reference other motifs; circular references are detected at
  compose time and raise FlorasValidationError with the cycle chain.
- `examples/枝.bloom`: combines 模様 + 散らす — 1 main sakura + 8 scattered
  "branch" motifs each consisting of 1 sakura + 2 buds.

### Changed
- All flower (`花`) names in shipped examples are now hiragana / katakana
  only:
  桜 → さくら, 薔薇 → ばら, 菊 → きく, コスモス → こすもす, 百合 → ゆり,
  花弁 → かべん, 主役桜 → しゅやくざくら.
- Filenames renamed accordingly: `examples/{さくら,ばら,きく,こすもす,ゆり}.bloom`.
- The lexer now accepts a leading `-` followed by a digit as a negative
  number literal so motif coordinates like `(-50, -30)` parse correctly.

### Tests
- 8 new tests cover motif decl, motif at center, unknown target,
  circular references, scatter-of-motif expansion, and the negative number
  literal. All 80 tests pass; ruff/mypy strict 0 errors.

## [0.4.0] - 2026-05-07

### Changed — Language surface is now fully Japanese
The DSL surface no longer contains any ASCII alphabet. Every keyword,
identifier, numeric suffix, colour literal, and comment marker is expressed in
Japanese (CJK Han / Hiragana / Katakana / `※` / `×`). Alphabet remains only
inside string literals (file paths in `書出 ... へ "..."`) and in tooling
output such as the SVG itself.

Old → new mapping (highlights):
- `palette` → `色見本`, `bloom` → `花`, `bouquet` → `花束`, `export` → `書出`
- `canvas` → `画布`, `background` → `背景`, `place` → `置く`, `at` → `に`
- `scatter` → `散らす`, `source` → `元`, `count` → `数`, `area` → `領域`,
  `seed` → `種`
- `petals` → `花弁数`, `petal-curl` → `花弁反り`, `petal-notch` → `花弁切込`,
  `stamen-count` → `雄蕊数`, `stem` → `茎`, `leaf-count` → `葉数`,
  `arrange` → `並び`, `tinted` → `混ぜ`, `width` → `幅`
- `ring` → `輪`, `spiral` → `螺旋`, `rect` → `矩形`, `grid` → `格子`
- `center` → `中央`, `auto` → `自動`, `random` → `乱数`,
  `true/false/none` → `真/偽/無`
- `12px` → `12点`, `90deg` → `90度`, `0.25turn` → `0.25周`
- Comment marker `shion ...` → `※ ...`
- Canvas separator `1200 x 630` → `1200 × 630` (U+00D7)

The hex colour literal (`#FFB7C5`) is removed entirely — every colour is now
either an OKLCH literal `知覚色(L C H)` or a palette reference `名前.要素`.

### Added — Scatter (procedural placement)
- `散らす { 元 花名; 数 N; 領域 ...; 種 N; }` inside a `花束`. Required `種`
  keeps the output deterministic across runs.
- Areas: `画布`, `輪 中央 (cx, cy) 内 r1 外 r2`,
  `矩形 (x1, y1) へ (x2, y2)`, `格子 列 N 行 M`.
- Optional per-scatter overrides: `大きさ`, `回転` (with `乱数` shorthand),
  `色`.
- `examples/桜吹雪.bloom`: 60 scattered petals + a centre sakura on a
  1200×630 canvas — a real "cherry blossom storm" hero image in 30 lines.

### Added — Tests
- 12 new tests cover Japanese tokens, scatter areas, deterministic seeds,
  scatter ranges, missing-seed errors, and an end-to-end alphabet check that
  asserts no example contains any A-Z character outside string literals.
- All 72 tests pass; coverage 88%; ruff and mypy strict both green.

### Removed
- All hex colour literal handling and the corresponding lexer / parser paths.
- The `shion`, `bara_kuchi`, `bara_tojiru` tokens and every English keyword.

## [0.3.0] - 2026-05-07

### Added
- `bouquet` declaration: top-level construct that renders multiple blooms onto a
  single canvas. Syntax:
  ```bloom
  bouquet hero {
    canvas 1200 x 630;
    background haru.cream;
    place yuri at (380, 320);
    place sakura at center { size 280; color haru.pink; };
  }
  ```
- `canvas <W> x <H>;` declares the SVG `viewBox`.
- `background <color>;` paints a full-canvas rectangle behind all blooms.
- `place <bloom> at (x, y);` and `place <bloom> at center;` for explicit and
  centred placements.
- Optional `{ … overrides; … }` block per `place` so a single bloom decl can be
  reused at different sizes / colours / strokes within one bouquet.
- CLI `--entry <name>` resolves to a bouquet when ambiguous; a single bouquet
  among helper blooms is the default entry without `--entry`.
- `examples/hero.bloom` — 1200×630 hero with a yuri + 3 sakura on a paper
  background.
- 5 new tests covering bouquet / placement / `at center` / overrides /
  unknown-bloom errors / single-bouquet entry inference.
- `docs/build_gallery.py` produces a self-contained `docs/gallery.html` showing
  every example with its source code.

## [0.1.0] - 2026-05-07

### Floras pivot
This release replaces the previous "general-purpose flower-named programming
language" experiment with a focused designer DSL: **Floras Bloom**. The old
language implementation is preserved at git tag/commit `4755d9f` for reference;
the spec under `.claude/specs/language-core/` is marked SUPERSEDED.

### Added
- `.bloom` source format with `palette`, `bloom`, and `export` top-level
  declarations.
- Lexer with numeric suffixes (`12px` / `50%` / `90deg` / `0.25turn`),
  hex colours (`#FFB7C5` / `#FFB7C5AA` / 3- and 4-digit shorthands),
  range operator `..`, and `oklch(L C H)` literals.
- Parser building a typed AST (`PaletteDecl`, `BloomDecl`, `ExportDecl`,
  values of type number / percent / angle / colour / palette-ref).
- Pure-function geometry primitives: petal (with curl + notch), stamen ring,
  leaf, stem.
- Compose pipeline that resolves palette references and validates property
  ranges before rendering.
- Standard-library OKLCH → sRGB conversion (Björn Ottosson, 2020).
- Tinted blends: `color brand.500 tinted brand.50 0.3`.
- SVG renderer producing `viewBox`-anchored output with coordinates rounded
  to 2 decimal places and deterministic byte-identical output.
- CLI: `floras render <file> [--out <path>] [--entry <name>] [--ast]` and
  `floras --version`.
- Five example flowers in `examples/`: sakura, bara, kiku, cosmos, yuri.
- 60 tests covering lexer, parser, geometry, compose, render, CLI, and E2E.

### Removed
- The previous tree-walking interpreter and all related infrastructure
  (lexer/parser/evaluator/REPL) for the general-purpose flower language.
