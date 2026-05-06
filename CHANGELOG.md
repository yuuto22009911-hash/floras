# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
