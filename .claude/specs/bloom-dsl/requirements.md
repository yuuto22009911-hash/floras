# Floras Bloom DSL — Requirements

| 項目 | 値 |
|------|-----|
| Status | Draft / In Review / **Approved** |
| Author | yuuto |
| Reviewer | yuuto (個人ポートフォリオのため自己レビュー) |
| Last Updated | 2026-05-07 |
| Approved On | 2026-05-07 |

> 本書中の MUST / MUST NOT / SHOULD / SHOULD NOT / MAY は RFC 2119 に従う。

## TL;DR
- **What**: 花を**宣言的に描き、束ね、procedural に配置**して、SVG / HTML / CSS に出力するデザイナー向け DSL。
- **Why**: Web デザイン現場で頻出する「花の絵」を、Figma に依存せず・コードで再利用・量産可能にする。Tailwind がスタイルに対して提供したものを、装飾フローラルアセットに対して提供する。
- **Success**: v1.0.0 リリース時点で、(1) `examples/sakura.bloom` を `floras render` で SVG に変換できる (2) `examples/hero.bloom` で 1200×630 のヒーロー画像が生成できる (3) MonoFloras 公式サイトの装飾アセット 3 点以上を本 DSL で生成し置き換える (4) GitHub Star 50+ を 3 ヶ月で獲得する。

## Background
- 個人ブランド MonoFloras の装飾アセット（桜・薔薇・コスモスのアイコン / パターン背景 / ヒーロー画像）を、Figma 手作業で量産するのが非効率だった。
- 既存の SVG 編集ツール (Inkscape / Figma) はスケール・色替え・大量生成が苦手。
- L-system 系（generative botany）は強力だが、デザイナーが学ぶには参入障壁が高い。
- **Tailwind** が「stylesheet をデザインシステム化」したように、**装飾アセット**もデザインシステム化する余地がある — それが Floras Bloom。
- 旧 spec (`.claude/specs/language-core/`) で「全構文を花名にする汎用言語」を v0.1.0 まで実装済み (`4755d9f`)。Lexer / Parser インフラは流用可能。

## Goals
- **G1** (v0.1.0): 単一の `bloom` 定義から SVG ファイルを 1 つ出力する。`floras render <file>.bloom --out <out>.svg` で完結。
- **G2** (Always): SVG 出力は `viewBox` 必須・座標小数点 2 桁丸め・決定論的（同じ `.bloom` は bit-identical な SVG）。
- **G3** (v0.2.0): `palette` でデザイントークン（色・寸法）を一括管理。`brand.500` のようなドット参照を解決。
- **G4** (v0.3.0): `bouquet` で複数 bloom を 1 キャンバス上に構成 (`place <bloom> at (x, y)`)。
- **G5** (v0.4.0): `scatter` で N 個の bloom を `radius`・`area`・`grid` 等のルールに従って procedural 配置。`seed` 必須。
- **G6** (v0.5.0): `motif` で再利用可能パターン（葉と花の組み合わせ等）を定義し、`scatter` や `bouquet` から呼び出せる。
- **G7** (v0.6.0): `floras preview <dir>` でローカルブラウザに SVG 一覧 + ファイル変更で自動再描画。
- **G8** (v0.7.0): `floras tokens <file>.bloom --out tokens.css` で `palette` を CSS Custom Properties に書き出す。Tailwind の `theme.extend.colors` 形式 (`tokens.json`) も MAY 出力。
- **G9** (v1.0.0): Web プレイグラウンド (Pyodide) — `https://floras.dev/play`（仮）でブラウザだけで `.bloom` を編集 → SVG プレビュー。
- **G10** (Always): MonoFloras 公式サイトで生成 SVG を実利用する（dogfooding）。

## Non-Goals
- **NG1**: ピクセル画像（PNG / JPG）の直接出力。SVG → PNG は `librsvg` などの外部ツールで行う前提。
- **NG2**: 動的アニメーション（Lottie / SMIL）。SVG 内に `<animate>` を入れない（v1.5.0 で再検討）。
- **NG3**: 制御構文（if / while / for ループ）。デザインの「分岐」は `palette` 切替や複数 `bouquet` で表現する。チューリング完全性は不要。
- **NG4**: ベクター編集 GUI（旧 Inkscape 的なもの）。あくまでコード DSL。
- **NG5**: 写実的な花の描画。あくまで**装飾的・抽象的・幾何学的**な花。リアル花の写真を求めるユーザーには本 DSL は向かない。
- **NG6**: ラスター画像のインポート / トレース。SVG 入力すらサポートしない（v0.1.0）。
- **NG7**: 3D / WebGL レンダリング。
- **NG8**: 任意の外部 HTTP fetch / ファイル I/O 機能（サンドボックス維持）。

## User Stories

### US-01: ひとつの花を SVG で書き出す
**As a** Web デザイナー, **I want** `.bloom` ファイルに花の構造を書いて `floras render` で SVG が得られる, **so that** Figma を開かずにブランドアイコンを量産できる。

**Acceptance Criteria** (Given-When-Then):
- **AC-01-1**: **Given** `bloom sakura { petals 5; size 200; color #FFB7C5; }` を含む `sakura.bloom`, **When** `floras render sakura.bloom --out sakura.svg`, **Then** 200×200 viewBox の SVG が出力され、5 弁の桜形が描画される（path 要素 5 つ）。終了コード 0。
- **AC-01-2**: **Given** 同じ `.bloom` を 2 回 render, **When** 出力 SVG を `diff`, **Then** 完全一致（決定論性）。
- **AC-01-3**: **Given** 存在しない `.bloom` ファイルパス, **When** render, **Then** `Floras Error: file not found: <path>` を stderr に出し、終了コード 2。
- **AC-01-4**: **Given** 文法エラー含む `.bloom`, **When** render, **Then** `Floras SyntaxError at line N: <expected> but got <actual>` を出し、終了コード 1。

### US-02: 花の構造を細かく制御する
**As a** デザイナー, **I want** 花弁数・反り・切れ込み・雄しべ数・茎の有無を 1 ファイル内で調整できる, **so that** 同じ言語で「桜」「梅」「コスモス」のように異なる花を作り分けられる。

**Acceptance Criteria**:
- **AC-02-1**: **Given** `petals 8; petal-width 22; petal-height 30; curl 0.5; notch 0.0; stamen-count 24` を持つ bloom, **When** render, **Then** 各パラメータが SVG path 計算に反映される（snapshot test で固定）。
- **AC-02-2**: **Given** `petals 0`, **When** render, **Then** `Floras ValidationError: 'petals' must be at least 1` を出し終了コード 1。
- **AC-02-3**: **Given** `curl -0.1`（負の値）, **When** render, **Then** `Floras ValidationError: 'curl' must be in [0, 1]`。
- **AC-02-4**: **Given** `stem true; stem-length 80; leaf-count 2`, **When** render, **Then** 花の下に直線 path（茎）と 2 個の葉 path が追加される。

### US-03: パレットでブランド色を管理する (v0.2.0 / G3)
**As a** ブランドオーナー, **I want** ブランド色を `palette monofloras { ... }` で 1 箇所に書き、bloom から `color brand.500` で参照できる, **so that** ブランドの色変更が 1 ファイル修正で全アセットに伝播する。

**Acceptance Criteria**:
- **AC-03-1**: **Given** `palette brand { 500 #FFB7C5; 700 #C58E96; }` と `bloom sakura { color brand.500; }`, **When** render, **Then** SVG 内の fill が `#FFB7C5` になる。
- **AC-03-2**: **Given** 未定義トークン `color brand.999`, **When** render, **Then** `Floras NameError at line N: palette token 'brand.999' is not defined`。
- **AC-03-3**: **Given** 同名 palette が 2 回宣言された場合, **When** render, **Then** `Floras NameError: palette 'brand' is already defined`。
- **AC-03-4**: **Given** `oklch(0.78 0.13 12)` 形式の色値, **When** render, **Then** SVG fill 属性にそのまま出力される（モダンブラウザ前提）。

### US-04: 複数の花を構成する (v0.3.0 / G4)
**As a** デザイナー, **I want** `bouquet hero { place sakura at (200, 300); place bara at (600, 300); }` のように複数 bloom をキャンバスに配置できる, **so that** ヒーロー画像 1 枚を 1 ファイルで宣言できる。

**Acceptance Criteria**:
- **AC-04-1**: **Given** 2 つの bloom と `bouquet hero { canvas 1200 x 630; place sakura at (300, 315) size 240; place bara at (900, 315) size 240; }`, **When** `floras render hero.bloom --out hero.svg`, **Then** 1200×630 viewBox 内に 2 つの flower group `<g>` が指定座標に置かれる。
- **AC-04-2**: **Given** `place undefined_bloom at (0, 0)`, **When** render, **Then** `Floras NameError: bloom 'undefined_bloom' is not defined`。
- **AC-04-3**: **Given** `place sakura at center` ショートカット, **When** render, **Then** canvas 中央に配置（`(canvas.width/2, canvas.height/2)`）。
- **AC-04-4**: **Given** `bouquet` 内に `background brand.50;` 指定, **When** render, **Then** SVG ルートに `<rect fill="..."/>` が canvas 全体を覆って配置される。

### US-05: 花を散らす (v0.4.0 / G5)
**As a** デザイナー, **I want** 花弁を背景にランダムに散らせる, **so that** 単調な背景に手描き感のある装飾を加えられる。

**Acceptance Criteria**:
- **AC-05-1**: **Given** `scatter petals { source sakura; count 24; area canvas; size 12..32; rotation random; seed 42; }`, **When** render, **Then** 24 個の sakura が canvas 全体に散らばり、各サイズが 12〜32 の範囲で再現可能（同じ seed なら毎回同じ結果）。
- **AC-05-2**: **Given** `seed` 未指定, **When** render, **Then** `Floras ValidationError: 'scatter' requires explicit 'seed' for determinism`。
- **AC-05-3**: **Given** `area ring center (600, 315) inner 200 outer 320; count 12;`, **When** render, **Then** 12 個が指定リング内にのみ配置される（中心からの距離が 200〜320）。
- **AC-05-4**: **Given** `area grid cols 6 rows 4; count auto;`, **When** render, **Then** 6×4=24 個が等間隔グリッドに配置される。`count` が `auto` のときはセル数に合わせる。

### US-06: モチーフを再利用する (v0.5.0 / G6)
**As a** デザイナー, **I want** 「桜＋葉２枚＋茎」の組み合わせを `motif spring_branch` として 1 単位で扱える, **so that** scatter / bouquet からまとめて呼び出せる。

**Acceptance Criteria**:
- **AC-06-1**: **Given** `motif spring_branch { sakura at (0, 0); leaf at (-20, 30); leaf at (20, 30); stem from (0, 80) to (0, 0); }` と `bouquet hero { place spring_branch at (300, 400); }`, **When** render, **Then** motif 内の 4 要素が `<g transform="translate(300, 400)">` でまとめて配置される。
- **AC-06-2**: **Given** `scatter twigs { source spring_branch; count 8; area canvas; seed 7; }`, **When** render, **Then** 8 個の motif が散布される（各 motif は `<g>` でグルーピング）。
- **AC-06-3**: **Given** motif が他の motif を参照する循環定義, **When** render, **Then** `Floras ValidationError: circular motif reference detected: spring_branch -> twigs -> spring_branch`。

### US-07: ファイル変更で即プレビューする (v0.6.0 / G7)
**As a** デザイナー, **I want** `floras preview .` でローカルブラウザを開き、`.bloom` を保存するたびに自動で再描画される, **so that** Figma の即時フィードバックに迫る編集体験が得られる。

**Acceptance Criteria**:
- **AC-07-1**: **Given** `examples/` ディレクトリで `floras preview examples/`, **When** ブラウザで `http://localhost:7878` を開く, **Then** 配下の全 `.bloom` ファイルがサムネイル一覧で表示される。
- **AC-07-2**: **Given** プレビュー起動中に `examples/sakura.bloom` を編集して保存, **When** 1 秒以内, **Then** ブラウザのサムネイルが自動更新される（ポーリングまたは EventSource）。
- **AC-07-3**: **Given** ポート 7878 が使用中, **When** preview 起動, **Then** 7879 / 7880 ... と次の空きを試み、最終的に使用したポートを stderr に表示。
- **AC-07-4**: **Given** `.bloom` に文法エラー, **When** プレビュー再描画, **Then** 該当サムネイル位置に赤枠でエラーメッセージが表示される（プレビューサーバはクラッシュしない）。

### US-08: パレットを CSS 変数に書き出す (v0.7.0 / G8)
**As a** フロントエンド開発者, **I want** `floras tokens brand.bloom --out tokens.css` で palette を CSS Custom Properties に書き出せる, **so that** 同じブランド色を React コンポーネントからも参照できる。

**Acceptance Criteria**:
- **AC-08-1**: **Given** `palette brand { 500 #FFB7C5; 700 #C58E96; }`, **When** `floras tokens brand.bloom --out tokens.css`, **Then** `tokens.css` に `:root { --brand-500: #FFB7C5; --brand-700: #C58E96; }` が出力される。
- **AC-08-2**: **Given** `--format tailwind` フラグ, **When** 同コマンド, **Then** Tailwind v4 互換の `@theme { --color-brand-500: ...; }` 形式で出力される。
- **AC-08-3**: **Given** `--format json` フラグ, **When** 実行, **Then** JSON 形式 `{"brand": {"500": "#FFB7C5", ...}}` で出力。

### US-09: ブラウザだけで試す (v1.0.0 / G9)
**As a** 興味を持った訪問者, **I want** インストール不要でブラウザから `.bloom` を編集 → SVG プレビューできる, **so that** 言語の体験敷居を最小化できる。

**Acceptance Criteria**:
- **AC-09-1**: **Given** モダンブラウザで `https://<host>/play` を開く, **When** ページ読込完了, **Then** 左にエディタ、右に SVG プレビュー、上部に「Render / Tokens / Share / Sample」ボタンが表示される（初回 LCP < 3.0s）。
- **AC-09-2**: **Given** エディタにサンプル `sakura.bloom` がプリセット, **When** Render を押す, **Then** Pyodide で実行され、3 秒以内に右ペインに SVG プレビューが表示される。
- **AC-09-3**: **Given** Share ボタン押下, **When** 押す, **Then** 現在のコードが URL ハッシュ (`#code=base64`) にエンコードされ、URL がクリップボードにコピーされる。
- **AC-09-4**: **Given** Share URL から開く, **When** ページ読込, **Then** デコードされたコードがエディタに復元され、自動 Render される。

## Functional Requirements (EARS)
| ID | パターン | 要件 |
|----|---------|------|
| **FR-01** | Ubiquitous | The Floras lexer SHALL tokenize `.bloom` source into tokens whose `kind` corresponds to the keyword map (Glossary 参照). |
| **FR-02** | Ubiquitous | The Floras parser SHALL build an AST conforming to the EBNF in `design.md`. |
| **FR-03** | Ubiquitous | The compose pipeline SHALL resolve all symbol references (palette tokens / bloom names / motif names) before rendering, raising `FlorasNameError` for any unresolved reference. |
| **FR-04** | Event-driven | When `floras render <file> --out <path>` is invoked, the system SHALL lex, parse, compose, and render exactly one SVG file to `<path>`. |
| **FR-05** | Event-driven | When the AST contains exactly one top-level renderable (a `bloom` or `bouquet` or `motif`), the renderer SHALL use it as the entry. If multiple are present, the system SHALL require `--entry <name>`. |
| **FR-06** | Ubiquitous | All SVG output SHALL include `viewBox`, `xmlns="http://www.w3.org/2000/svg"`, and coordinate values rounded to 2 decimal places. |
| **FR-07** | Ubiquitous | All numeric coordinates and dimensions SHALL be representable as SVG-compatible values; angles in degrees, lengths in user units (px equivalent). |
| **FR-08** | Event-driven | When a `scatter` is evaluated, the system SHALL use a deterministic PRNG seeded by the `seed` value; the same `.bloom` MUST produce a bit-identical SVG across runs. |
| **FR-09** | Unwanted | If `scatter` is declared without an explicit `seed`, the system SHALL raise `FlorasValidationError`. |
| **FR-10** | Ubiquitous | All errors raised during lex / parse / compose / render SHALL include 1-origin source line numbers and SHALL be subclasses of `FlorasError`. |
| **FR-11** | Optional | Where the `--ast` flag is given to `floras render`, the system SHALL print the resolved scene graph as JSON to stdout instead of writing SVG. |
| **FR-12** | State-driven | While `floras preview <dir>` is running, the system SHALL serve an HTTP page listing all `.bloom` files in `<dir>` and re-render them on file modification (inotify / fsevents / polling fallback). |
| **FR-13** | Event-driven | When `floras tokens <file> --out <out> --format <fmt>` is invoked with `fmt` ∈ {css, tailwind, json}, the system SHALL emit palette tokens in the chosen format. |
| **FR-14** | Ubiquitous | The Web Playground SHALL run `floras render` in-browser via Pyodide and emit SVG to a `<div>` without round-tripping to a backend. |
| **FR-15** | Unwanted | If a `.bloom` source attempts to import a file or perform OS-level I/O (none exists in the language), the parser SHALL fail at the unknown keyword. |

## Non-Functional Requirements
| カテゴリ | 要件 | 測定方法 |
|---------|------|---------|
| Performance | 単一 bloom render < 50ms (M1 Mac) | `time floras render` |
| Performance | 100 個の bloom を含む bouquet render < 200ms | ベンチスクリプト |
| Performance | preview サーバ起動から初回ブラウザ表示まで < 1s | E2E |
| Performance | playground LCP < 3.0s（4G 想定） | Lighthouse |
| Output 品質 | SVG ファイルサイズ: 単一 bloom < 4KB（gzip 前） | snapshot |
| Output 品質 | 出力 SVG が Inkscape / Illustrator / Figma で開ける | 手動確認（CI 不可） |
| Determinism | 同じ `.bloom` + 同じバージョンは bit-identical SVG | E2E diff |
| メモリ | render 中の RSS < 64MB（典型サンプル） | `ps -o rss` |
| エラー品質 | 全エラーは「行番号 + トークン + 期待値」を含む | テストで全エラー型を検証 |
| テストカバレッジ | 主要モジュール (lexer / parser / geometry / compose / render) line coverage 85% 以上 | `pytest --cov` |
| 型安全性 | `mypy --strict` でエラー 0 件 | CI |
| 対応環境 | macOS 14+ / Ubuntu 22.04+ / Windows 11 + Python 3.11+ | CI matrix |
| 対応ブラウザ | Chrome / Safari / Firefox 各最新 2 バージョン（preview / playground） | Playwright |
| アクセシビリティ | playground は WCAG 2.1 AA、キーボードのみで全操作可 | axe-core + 手動 |
| 依存 (Core) | Floras 本体は Python 標準ライブラリのみ | `pip-deptree` |
| 依存 (Playground) | Pyodide + Monaco Editor のみ（バンドル < 6MB gz） | `pnpm build` ログ |
| ドキュメント | README に 7 機能（bloom / palette / bouquet / scatter / motif / preview / tokens）の最小サンプル + ギャラリー | レビュー |

## Constraints
- 予算: ¥0（個人開発、ホスティングは Cloudflare Pages 無料枠）
- 納期: ソフトターゲット 2026-08-31（4 ヶ月）
- 既存システム制約: 旧 spec の `floras/__init__.py` `lexer.py` `tokens.py` `errors.py` のクラス構造は流用するが、AST と evaluator は完全に書き直す
- 倫理: コードはオープンソース（MIT、旧 spec から継承）

## Resolved Decisions
- [x] **D-01**: 出力ファイル拡張子は `.bloom`（旧 `.floras` から変更、デザイナーに直感的）。
- [x] **D-02**: ブロック区切りは `{ ... }`（旧 `ajisai ... kikyou` を採用しない、デザイナーの可読性優先）。
- [x] **D-03**: 文末は `;` （旧 `nadeshiko` を採用しない、同上）。
- [x] **D-04**: 制御構文（if/while/for）は v1.0.0 まで導入しない。`palette` 切替や複数 `bouquet` で「分岐」を表現する。
- [x] **D-05**: 数値リテラルは `42` `3.14` `12px` `50%` `0..1` (range) `random` `auto` の 6 種。範囲表記は `min..max` でランダムサンプリング (scatter 内のみ意味を持つ)。
- [x] **D-06**: 色リテラルは `#RRGGBB` `#RRGGBBAA` `oklch(L C H)` `palette.token` 参照の 4 種。`rgb()` `hsl()` は v1.0.0 では非対応（`oklch` を主軸に）。
- [x] **D-07**: 座標系は SVG 標準（左上原点、Y 下向き）。`at center` は canvas 中央のショートカット。
- [x] **D-08**: 角度は度数法 `90deg`、`turn` も許容（`0.25turn` = 90deg）。ラジアンは非対応。
- [x] **D-09**: ライセンス MIT（旧 spec から継承）。
- [x] **D-10**: ホスティング Cloudflare Pages、ドメイン `floras.dev`（旧 spec から継承）。
- [x] **D-11**: 旧言語との関係: 旧 v0.1.0 コードは `4755d9f` 時点の git tree として残し、新 spec 着手時に `floras/` 内のソースは削除して書き直す。examples / tests も同時に書き直し。

## Glossary — Floras Bloom DSL Token Map

### Top-level Keywords / トップレベル宣言
| Token | 役割 | 例 |
|-------|------|-----|
| `palette` | 色トークン定義 | `palette brand { 500 #FFB7C5; }` |
| `bloom`   | 単一の花の構造定義 | `bloom sakura { petals 5; }` |
| `motif`   | 再利用可能な複合パターン | `motif branch { sakura at (0, 0); leaf at (10, 30); }` |
| `bouquet` | キャンバス上の構成（シーン） | `bouquet hero { canvas 1200 x 630; place sakura at center; }` |

### Statement Keywords / 内部キーワード
| Token | 役割 | 使われる場所 |
|-------|------|-------------|
| `canvas` | キャンバスサイズ宣言 | bouquet 内 |
| `background` | 背景色 | bouquet 内 |
| `place` | 単一配置 | bouquet, motif 内 |
| `at` | 座標指定（`at (x, y)` / `at center`） | place, scatter |
| `scatter` | procedural 配置 | bouquet 内 |
| `source` | scatter 内で散布する bloom / motif 名 | scatter 内 |
| `count` | scatter / area の個数 | scatter 内 |
| `area` | scatter の配置領域 | scatter 内 |
| `seed` | 乱数シード | scatter 内 |
| `size` | サイズ（数値 or range） | place / scatter / bloom 内 |
| `rotation` | 回転（角度 or `random`） | place / scatter |
| `color` | 色（hex / oklch / palette ref） | bloom / palette / scatter 内 |
| `stroke` | 線（色 + 幅） | bloom 内 |
| `width` | 線の太さ / canvas 幅 | stroke / canvas |
| `height` | canvas 高さ | canvas |
| `from` / `to` | 線分の起点・終点 | stem 等 |
| `petals` | 花弁数 | bloom 内 |
| `petal-width` / `petal-height` / `petal-curl` / `petal-notch` | 花弁形状パラメータ | bloom 内 |
| `stamen-count` / `stamen-radius` / `stamen-color` | 雄しべ | bloom 内 |
| `stem` / `stem-length` / `stem-color` | 茎 | bloom 内 |
| `leaf-count` | 葉の枚数 | bloom 内 |
| `arrange` | 花弁の配置パターン (`ring` / `spiral`) | bloom 内 |
| `tinted` | 色をブレンド `color brand.500 tinted paper 0.3` | bloom / scatter |
| `export` | 出力先指定（CLI で `--out` を省略する場合の代替） | top-level |

### Area Sub-Keywords / 散布領域
| Token | 意味 |
|-------|------|
| `canvas` | bouquet の全領域 |
| `ring` | 中心 + 内径 + 外径で定義された円環 |
| `rect` | 矩形領域 `rect (x1, y1) to (x2, y2)` |
| `grid` | 等間隔グリッド `grid cols N rows M` |
| `path` | 任意の SVG path に沿って配置（v1.0.0 では非対応、予約） |

### Arrange Sub-Keywords / 花弁配置
| Token | 意味 |
|-------|------|
| `ring` | 等間隔円配置（既定） |
| `spiral` | 黄金角螺旋（バラ等）`arrange spiral { rotation 137.5deg; }` |

### Built-in Constants / 組み込み定数
| Token | 値 |
|-------|-----|
| `center` | canvas 中央座標 |
| `auto` | 自動算出（grid の count 等） |
| `random` | 乱数（要 seed） |
| `true` / `false` | 真偽値 |
| `none` | null / 未指定 |

### Numeric Literal / 数値リテラル
| 形式 | 例 | 意味 |
|------|-----|------|
| 整数 | `42` | 数値（単位なし、user unit） |
| 浮動小数 | `3.14` | 数値 |
| px | `12px` | ピクセル（user unit と等価） |
| 百分率 | `50%` | 親要素相対 |
| 角度 | `90deg` `0.25turn` | 角度 |
| 範囲 | `12..32` | scatter 内で min..max ランダムサンプル |

### Color Literal / 色リテラル
| 形式 | 例 |
|------|-----|
| hex | `#FFB7C5` `#FFB7C5AA` |
| oklch | `oklch(0.78 0.13 12)` |
| palette ref | `brand.500` `brand.500 tinted paper 0.3` |

### Comment / コメント
| 形式 | 例 |
|------|-----|
| 行コメント | `shion this is a comment`（旧仕様継承）|

### Punctuation / 記号
| Token | 役割 |
|-------|------|
| `{` `}` | ブロック |
| `(` `)` | 座標タプル / グルーピング |
| `;` | 文末 |
| `,` | 引数区切り |
| `..` | 範囲（数値リテラル） |
| `.` | palette token のドット参照 |
| `x` | canvas サイズ表記の連結 (`1200 x 630`) — 二項演算子ではなく予約 token |

> **凡例**: ユーザー識別子は `[a-zA-Z_][a-zA-Z0-9_-]*`。上記キーワードと衝突する識別子は MUST 拒否（FR-01）。
