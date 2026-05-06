# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
