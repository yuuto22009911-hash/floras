# Floras Language Core — Requirements

| 項目 | 値 |
|------|-----|
| Status | Draft / In Review / **Approved** |
| Author | yuuto |
| Reviewer | yuuto (個人ポートフォリオのため自己レビュー) |
| Last Updated | 2026-05-03 |
| Approved On | 2026-05-03 (全 Open Questions 解決済み) |

> 本書中の MUST / MUST NOT / SHOULD / SHOULD NOT / MAY は RFC 2119 に従う。

## TL;DR
- **What**: すべての構文要素を花の名前で構成する Python 製インタプリタ言語「Floras」を、**7 つの差別化機能**（花言葉エラー / 花占い演算子 / kafun テスト DSL / 季節モード / floras garden AST 可視化 / kareru ライフタイム / Web プレイグラウンド）込みで構築する。
- **Why**: 言語処理系の学習価値と、MonoFloras と地続きの世界観を持つポートフォリオ作品としての話題性を最大化する。
- **Success**: v1.0.0 リリース時点で、(1) `examples/fizzbuzz.floras` が動作 (2) 公開プレイグラウンド `https://floras.dev/play`（仮）で来訪者がブラウザだけで Floras を実行できる (3) GitHub Star 50+ を 3 ヶ月で獲得する。

## Background
- 言語処理系の知識を体系的に獲得したい。
- MonoFloras ブランドの世界観（花）と地続きの作品を持つことで、技術と感性の両軸を示すポートフォリオを構築したい。
- Lox / Monkey などの教材言語は多数あるが、**全構文を花名にした言語は前例がほぼ無い**ため、作品としての話題性が高い。

## Goals
- **G1** (v0.1.0): Core 言語仕様 — `let / fn / if/else / while / 比較 / 算術 / print / return / 関数呼び出し` を網羅。
- **G2** (Always): Lexer・Parser・Evaluator・付加機能の各層を**疎結合**に保ち、テストカバレッジ 85% 以上。
- **G3** (Always): README に Floras と一般言語の対照表 + 全機能のサンプルを掲載。
- **G4** (v0.1.0): `floras repl` で対話実行・行単位エラー位置出力。
- **G5** (v0.2.0): **花言葉エラー** — 全エラー種別に花言葉系の詩的な補助メッセージを添える。
- **G6** (v0.3.0): **花占い演算子 `kakitsubata`** — 非決定論的選択演算子で言語に「揺らぎ」を導入。
- **G7** (v0.4.0): **kafun テスト DSL** — `kafun` ブロックで言語内蔵テストを書けるようにし、`floras kafun` で実行・PASS/FAIL レポート。
- **G8** (v0.5.0): **季節モード** — `haru/natsu/aki/fuyu/toshi` の宣言で、その季節に咲く花トークンのみ使用可とする方言切替。
- **G9** (v0.6.0): **`floras garden` 可視化** — AST を ASCII / Mermaid / SVG の 3 形式で「花畑図」として描画。
- **G10** (v0.7.0): **`kareru` ライフタイム** — 明示解放と「世代カウンタ」による自動枯死で所有権概念の入門を提供。
- **G11** (v1.0.0): **Web プレイグラウンド** — Pyodide で Floras を実行できるブラウザ環境を `https://floras.dev/play`（仮）で公開。
- **G12** (v1.0.0): GitHub Star 50+ / Twitter 200 いいね相当 / Hacker News または Reddit 露出 1 回以上。

## Non-Goals
- **NG1**: クラス・継承・メソッド構文（v2.0.0 以降）。
- **NG2**: 配列・辞書・高階関数の**完全実装**（v0.2.0 で配列リテラルのみ予約、関数値は v1.5.0）。
- **NG3**: バイトコード VM 化・ネイティブコンパイル（学術プロジェクトとして将来検討）。
- **NG4**: 言語自体のパフォーマンス最適化（可読性・教材性優先）。
- **NG5**: VS Code 拡張・LSP（別 spec `editor-support`）。
- **NG6**: マルチバイト識別子（漢字変数名等）。識別子は ASCII 範囲のみ。
- **NG7**: ファイル I/O・ネットワーク・OS 連携 API（サンドボックス維持のため）。
- **NG8**: Web プレイグラウンドのバックエンド機能（共有 URL / ユーザーアカウント等は v1.1.0 以降）。

## User Stories

### US-01: スクリプトを実行する
**As a** Floras を試す開発者, **I want** `.floras` ファイルを CLI から実行できる, **so that** プログラムの動作確認ができる。

**Acceptance Criteria** (Given-When-Then):
- **AC-01-1**: **Given** 文法的に正しい `hello.floras` がある, **When** `floras run hello.floras` を実行する, **Then** 期待される標準出力が表示され、終了コード 0 を返す。
- **AC-01-2**: **Given** 存在しないファイルパスを渡す, **When** `floras run notfound.floras` を実行する, **Then** `Floras Error: file not found: notfound.floras` を stderr に出し、終了コード 2 を返す。
- **AC-01-3**: **Given** 文法エラーを含む `.floras` ファイル, **When** 実行する, **Then** `Floras SyntaxError at line N: <expected> but got <actual>` を出し、終了コード 1 を返す。

### US-02: 変数と算術を扱う
**As a** Floras 利用者, **I want** 変数宣言と四則演算ができる, **so that** 計算プログラムが書ける。

**Acceptance Criteria**:
- **AC-02-1**: **Given** `sakura x tsuyukusa 2 momo 3 nadeshiko botan kobushi x mokuren nadeshiko`, **When** 実行する, **Then** 標準出力に `5` が表示される。
- **AC-02-2**: **Given** 未宣言変数を参照する `botan kobushi y mokuren nadeshiko`, **When** 実行する, **Then** `Floras NameError at line 1: 'y' is not defined` を出し、終了コード 1 を返す。
- **AC-02-3**: **Given** ゼロ除算 `botan kobushi 1 suzuran 0 mokuren nadeshiko`, **When** 実行する, **Then** `Floras RuntimeError at line 1: division by zero` を出し、終了コード 1 を返す。

### US-03: 条件分岐を扱う
**As a** Floras 利用者, **I want** if/else が書ける, **so that** 条件によって挙動を変えられる。

**Acceptance Criteria**:
- **AC-03-1**: **Given** `bara kobushi 1 fukujusou 2 mokuren ajisai botan kobushi bara_kuchi yes bara_tojiru mokuren nadeshiko kikyou`, **When** 実行する, **Then** 標準出力に `yes` が表示される。
- **AC-03-2**: **Given** else 句を含む式で false 側に分岐する条件, **When** 実行する, **Then** else ブロック内の文だけが実行される。
- **AC-03-3**: **Given** if の条件式が真偽値以外（例: 数値）を返す, **When** 実行する, **Then** truthy ルールに従い、0 と `tanpopo` のみ偽、それ以外は真として動作する。

### US-04: ループを扱う
**As a** Floras 利用者, **I want** while ループが書ける, **so that** 繰り返し処理ができる。

**Acceptance Criteria**:
- **AC-04-1**: **Given** カウンタを 1 から 5 まで `botan` する while プログラム, **When** 実行する, **Then** 1〜5 が改行区切りで標準出力される。
- **AC-04-2**: **Given** `examples/fizzbuzz.floras`（後述の参考実装）, **When** 実行する, **Then** 標準 FizzBuzz の出力（1〜15 行）と完全一致する。
- **AC-04-3**: **Given** while の条件が常に真でループ回数が 100,000 を超える, **When** 実行する, **Then** 最大ループ深度の制約は MAY 実装（v0.1.0 では制約なし）。

### US-05: 関数を定義・呼び出す
**As a** Floras 利用者, **I want** 関数を定義して呼び出せる, **so that** 処理を再利用できる。

**Acceptance Criteria**:
- **AC-05-1**: **Given** `yuri add kobushi a kasumi b mokuren ajisai ran kobushi a momo b mokuren nadeshiko kikyou botan kobushi add kobushi 2 kasumi 3 mokuren mokuren nadeshiko`, **When** 実行する, **Then** 標準出力に `5` が表示される。
- **AC-05-2**: **Given** 引数の数が一致しない呼び出し, **When** 実行する, **Then** `Floras ArityError at line N: 'add' expects 2 args, got 1` を出し、終了コード 1 を返す。
- **AC-05-3**: **Given** 再帰関数 `fib(10)` を呼ぶ, **When** 実行する, **Then** 結果 `55` が出力される。

### US-06: REPL で試す
**As a** Floras 学習者, **I want** REPL で 1 行ずつ試せる, **so that** 文法を素早く習得できる。

**Acceptance Criteria**:
- **AC-06-1**: **Given** `floras repl` を起動した状態, **When** `botan kobushi 1 momo 1 mokuren nadeshiko` を入力, **Then** プロンプトに `2` が即座に表示される。
- **AC-06-2**: **Given** REPL で文法エラーを入力, **When** 確定する, **Then** 該当行のエラーメッセージを出し REPL は終了せず継続する。
- **AC-06-3**: **Given** REPL で `Ctrl-D` を入力, **When** 押下, **Then** REPL が終了コード 0 で終わる。

### US-07: 花言葉エラーで詩的に学ぶ (v0.2.0 / G5)
**As a** Floras 学習者, **I want** エラーメッセージに花言葉が添えられている, **so that** 単なるエラーではなく Floras の世界観を体感しながら原因を理解できる。

**Acceptance Criteria**:
- **AC-07-1**: **Given** 未定義変数を参照するコード, **When** 実行する, **Then** stderr に `Floras NameError at line N: 'x' is not defined\n  ※ 勿忘草の願い ─ この名前は記憶されていません` のように 2 行目に該当エラー型に紐づく花言葉メッセージが付与される。
- **AC-07-2**: **Given** `--no-poesy` フラグを付けて実行, **When** 同じエラーを起こす, **Then** 花言葉行は出力されず従来通りの 1 行エラーになる。
- **AC-07-3**: **Given** 全 6 エラー型（Syntax/Name/Type/Arity/Runtime/Internal）, **When** それぞれを発生させる, **Then** 各型に固有の花言葉メッセージが返る（重複なし）。

### US-08: 花占い演算子で揺らぎを楽しむ (v0.3.0 / G6)
**As a** Floras 利用者, **I want** `kakitsubata` 演算子で複数候補から無作為に 1 つ選べる, **so that** 占い・ガチャ・サンプル選定など遊びを書ける。

**Acceptance Criteria**:
- **AC-08-1**: **Given** `botan kobushi bara_kuchi A bara_tojiru kakitsubata bara_kuchi B bara_tojiru kakitsubata bara_kuchi C bara_tojiru mokuren nadeshiko` を 100 回実行, **When** 各回の出力を集計, **Then** A / B / C それぞれが少なくとも 10 回以上現れる（一様分布前提）。
- **AC-08-2**: **Given** `FLORAS_SEED=42` を設定して同じスクリプトを 2 回実行, **When** 出力を比較, **Then** 完全一致する（再現性のための seed 固定）。
- **AC-08-3**: **Given** `kakitsubata` を関数呼び出しと組み合わせる `f kobushi mokuren kakitsubata g kobushi mokuren`, **When** 実行する, **Then** 評価順は左 → 右、選ばれた式のみ副作用を起こす（短絡評価）。

### US-09: kafun テスト DSL でテストを書く (v0.4.0 / G7)
**As a** Floras 利用者, **I want** 言語に組み込まれた `kafun` ブロックでテストを書ける, **so that** 別の言語/フレームワークなしでテスト駆動開発できる。

**Acceptance Criteria**:
- **AC-09-1**: **Given** `kafun bara_kuchi fib(10) は 55 bara_tojiru ajisai fib kobushi 10 mokuren wasurenagusa 55 kikyou` を含むファイル, **When** `floras kafun examples/fib.floras`, **Then** `✓ fib(10) は 55` が出力され終了コード 0。
- **AC-09-2**: **Given** 失敗するアサーション, **When** `floras kafun`, **Then** `✗ <タイトル> at line N: expected <expected> but got <actual>` を出し終了コード 1。
- **AC-09-3**: **Given** ディレクトリを指定 `floras kafun examples/`, **When** 実行, **Then** 配下の全 `.floras` の `kafun` ブロックを集約実行し、最後に `Passed: M, Failed: N` のサマリを出す。
- **AC-09-4**: **Given** `floras run` で同じファイルを実行, **When** 実行, **Then** `kafun` ブロックは**スキップされる**（テスト副作用が通常実行に影響しない）。

### US-10: 季節モード（二十四節気）で方言を切り替える (v0.5.0 / G8 / D-07)
**As a** Floras 利用者, **I want** ファイル冒頭で二十四節気のいずれかを宣言すると、その節気の装飾花トークンだけが使える, **so that** 季語のような俳句的制約を持つコードが書ける。

**Acceptance Criteria**:
- **AC-10-1**: **Given** ファイル冒頭が `shunbun nadeshiko` で始まり、装飾花として `sakura` のみ使用, **When** 実行, **Then** 正常動作する（`shunbun` の追加許可リストに `sakura` を含むため）。
- **AC-10-2**: **Given** `shunbun nadeshiko` の後に `kiku`（菊、秋の `shuubun` の追加許可）を装飾的に使用, **When** 実行, **Then** `Floras SeasonError at line N: 'kiku' is not allowed in season 'shunbun'` を出し終了コード 1。
- **AC-10-3**: **Given** `toshi nadeshiko` を宣言、または何も宣言しない, **When** 全花トークンを使用, **Then** 制約なしで動作する（`toshi` がデフォルト）。
- **AC-10-4**: **Given** 季節宣言が複数ある（`shunbun nadeshiko` の後に `kanro nadeshiko`）, **When** パース, **Then** `Floras SyntaxError: duplicate season declaration` を出す。
- **AC-10-5**: **Given** ALWAYS_ALLOWED に含まれる全トークン（制御キーワード・記号・比較演算子・算術演算子・論理演算子・括弧・文字列ペア・数値リテラル・全 25 季節宣言トークン）, **When** いかなる節気宣言下で使用, **Then** **季節制約から除外されて常に使える**（言語が機能しなくなるため）。
- **AC-10-6**: **Given** 25 個の季節トークン（24 節気 + `toshi`）すべて, **When** 各々を冒頭で宣言する 25 ファイルを実行, **Then** どれもパースエラーを起こさず、それぞれの allow-list が適用される。

### US-11: floras garden で AST を花畑として見る (v0.6.0 / G9)
**As a** Floras 学習者, **I want** AST を花畑のような視覚で確認できる, **so that** 言語処理系の構造を直感的に理解できる。

**Acceptance Criteria**:
- **AC-11-1**: **Given** `examples/hello.floras`, **When** `floras garden examples/hello.floras --format ascii`, **Then** ノードに対応する花絵文字（🌸🌹🌼🪻🌷🌺）+ ツリー構造の ASCII が標準出力に表示される。
- **AC-11-2**: **Given** 同じファイル, **When** `--format mermaid`, **Then** Mermaid `graph TD` の DSL が出力され、コピペで `mermaid.live` に貼って描画できる。
- **AC-11-3**: **Given** 同じファイル, **When** `--format svg --output garden.svg`, **Then** `garden.svg` ファイルに花畑風 SVG（横並びの花レイアウト）が生成される。
- **AC-11-4**: **Given** 不正な `--format` 値, **When** 実行, **Then** `Floras CLIError: unsupported format 'xxx'. choose ascii/mermaid/svg` を出し終了コード 2。

### US-12: kareru で寿命を意識する (v0.7.0 / G10)
**As a** Floras 学習者, **I want** 変数を `kareru` で明示解放でき、放置した変数は世代カウンタで自動枯死する, **so that** 所有権・ライフタイムの概念を遊びながら学べる。

**Acceptance Criteria**:
- **AC-12-1**: **Given** `sakura tmp tsuyukusa 100 nadeshiko kareru tmp nadeshiko botan kobushi tmp mokuren nadeshiko`, **When** 実行, **Then** `Floras LifetimeError at line 3: 'tmp' has withered` を出し終了コード 1。
- **AC-12-2**: **Given** `FLORAS_LIFESPAN=10` を設定し、変数を作って 11 回 `botan` する, **When** 実行, **Then** 11 回目の参照で `LifetimeError` が出る。
- **AC-12-3**: **Given** `FLORAS_LIFESPAN=0`（無制限） or 環境変数未設定 default, **When** 任意のスクリプト, **Then** 自動枯死は発動せず従来通り動作する（後方互換）。
- **AC-12-4**: **Given** `kareru` の対象が未定義変数, **When** 実行, **Then** `Floras NameError at line N: cannot wither undefined name 'x'`。

### US-13: Web プレイグラウンドでブラウザ実行 (v1.0.0 / G11)
**As a** 興味を持った訪問者, **I want** インストール不要でブラウザから Floras を試せる, **so that** 言語の体験敷居を最小化できる。

**Acceptance Criteria**:
- **AC-13-1**: **Given** モダンブラウザ（Chrome/Safari/Firefox 最新）で `https://<host>/play` を開く, **When** ページ読込完了, **Then** 左にエディタ、右に出力ペイン、上部に「Run / Garden / Kafun / Share」ボタンが表示される（初回 LCP < 3.0s）。
- **AC-13-2**: **Given** エディタにサンプル `hello.floras` がプリセット, **When** 「Run」を押す, **Then** Pyodide 経由で Floras が実行され、3 秒以内に右ペインに `Hello, world` が表示される。
- **AC-13-3**: **Given** エディタに不正なコード, **When** Run, **Then** stderr 内容が右ペインに赤字で表示され（花言葉行も含む）、ページはクラッシュしない。
- **AC-13-4**: **Given** 「Garden」ボタン押下, **When** 実行, **Then** AST が SVG 花畑として描画される。
- **AC-13-5**: **Given** 「Share」ボタン押下, **When** 押す, **Then** 現在のコードが URL ハッシュ (`#code=base64`) にエンコードされ、URL がクリップボードにコピーされる（バックエンド不要）。

## Functional Requirements (EARS)
| ID | パターン | 要件 |
|----|---------|------|
| **FR-01** | Ubiquitous | The Floras lexer SHALL tokenize source into tokens whose `kind` corresponds to the flower-name token map (Glossary 参照). |
| **FR-02** | Ubiquitous | The Floras parser SHALL build an AST conforming to the grammar defined in `design.md`. |
| **FR-03** | Ubiquitous | The Floras evaluator SHALL execute the AST in a tree-walking interpreter manner with lexical scoping. |
| **FR-04** | Event-driven | When `floras run <file>` is invoked, the system SHALL read the file, lex, parse, evaluate, and exit with code 0 on success. |
| **FR-05** | Event-driven | When a syntax error is detected, the system SHALL emit `Floras SyntaxError at line N: ...` to stderr and exit with code 1. |
| **FR-06** | Event-driven | When a runtime error is detected, the system SHALL emit `Floras <Kind>Error at line N: ...` to stderr and exit with code 1. |
| **FR-07** | State-driven | While in REPL mode, the system SHALL accept input line-by-line and persist variable bindings across inputs until exit. |
| **FR-08** | Optional | Where the `--ast` flag is given to `floras run`, the system SHALL print the AST as JSON instead of executing. |
| **FR-09** | Unwanted | If the host Python raises an uncaught exception during evaluation, then the system SHALL wrap it as `Floras InternalError` and emit stderr with stack trace hidden by default. |
| **FR-10** | Ubiquitous | The Floras language SHALL reserve all flower-name tokens listed in Glossary as keywords (use as identifier MUST be rejected at parse time). |
| **FR-11** | Event-driven | When any `FlorasError` is raised, the system SHALL append a poesy line (花言葉) on a second stderr line **unless** `--no-poesy` flag is set. (US-07 / G5) |
| **FR-12** | Ubiquitous | The `kakitsubata` operator SHALL evaluate exactly one of its operands chosen uniformly at random; the unchosen operand MUST NOT be evaluated (short-circuit semantics). (US-08) |
| **FR-13** | State-driven | While the `FLORAS_SEED` env var is set to an integer, the random source for `kakitsubata` SHALL be deterministic across runs. (US-08 / AC-08-2) |
| **FR-14** | Event-driven | When `floras kafun <path>` is invoked, the system SHALL collect all `kafun` blocks under `<path>`, run each in an isolated environment, and emit a per-test result + final summary. (US-09) |
| **FR-15** | State-driven | While in `floras run` mode (not `kafun` mode), `kafun` blocks SHALL be parsed but NOT executed. (US-09 / AC-09-4) |
| **FR-16** | Optional | Where the first non-comment statement is a season declaration (`haru/natsu/aki/fuyu nadeshiko`), the lexer SHALL restrict subsequent flower tokens to that season's allowed set. (US-10) |
| **FR-17** | Unwanted | If a token outside the active season's allow-list appears (excluding control keywords and required symbols per AC-10-5), the system SHALL emit `Floras SeasonError`. (US-10 / AC-10-2) |
| **FR-18** | Event-driven | When `floras garden <path> --format <fmt>` is invoked, the system SHALL render the AST as ASCII / Mermaid / SVG and write to stdout (or `--output` file). (US-11) |
| **FR-19** | State-driven | While `FLORAS_LIFESPAN=N` (N>0), each variable SHALL be tracked by a generation counter and become `withered` after N evaluator steps without re-assignment; subsequent reads MUST raise `FlorasLifetimeError`. (US-12) |
| **FR-20** | Event-driven | When the user clicks "Run" in the Web Playground, the system SHALL execute the editor content via Pyodide-loaded Floras and stream stdout/stderr to the output pane within 3 seconds (typical scripts ≤ 100 lines). (US-13) |

## Non-Functional Requirements
| カテゴリ | 要件 | 測定方法 |
|---------|------|---------|
| Performance | `examples/fizzbuzz.floras` 実行時間 < 200ms (M1 Mac, cold start) | `time floras run` 計測 |
| Performance | `fib(20)` 再帰実行 < 2 秒 | ベンチスクリプト |
| Performance | `floras garden hello.floras --format svg` < 500ms | ベンチ |
| Performance | Web Playground 初回読込 LCP < 3.0s（4G 回線想定） | Lighthouse |
| Performance | Web Playground「Run」押下 → 出力描画 < 3.0s（典型 ≤100 行） | E2E 計測 |
| メモリ | スクリプト実行中の RSS < 64MB（典型的サンプル） | `ps -o rss` |
| メモリ | Pyodide ロード後のブラウザヒープ < 80MB | DevTools Profiler |
| エラー品質 | 全エラーは「行番号 + トークン + 期待値」を含み、`--no-poesy` 以外では花言葉行を伴う | テストで全エラー型を検証 |
| 決定論 | `FLORAS_SEED` 設定下で `kakitsubata` 含むスクリプトは bit-identical な出力を返す | E2E |
| テストカバレッジ | 主要モジュール (lexer/parser/evaluator/season/garden/kafun/lifecycle) line coverage 85% 以上 | `pytest --cov` |
| 型安全性 | `mypy --strict` でエラー 0 件（Web Playground の TypeScript も `tsc --strict`） | CI |
| 対応環境 | macOS 14+ / Ubuntu 22.04+ / Windows 11 + Python 3.11 以上 | CI matrix |
| 対応ブラウザ | Chrome / Safari / Firefox 各最新 2 バージョン | Playwright E2E |
| アクセシビリティ | Web Playground は WCAG 2.1 AA、キーボードのみで Run/Garden/Kafun 操作可 | axe-core + 手動 |
| 依存 (Core) | Floras 本体は Python 標準ライブラリのみ | `pip-deptree` |
| 依存 (Playground) | Pyodide + Monaco Editor のみ（バンドル < 6MB gz 後） | `pnpm build` ログ |
| ドキュメント | README に対照表 + 7 機能ごとのサンプル（最低各 1） | レビュー |

## Constraints
- 予算: ¥0（個人開発）
- 納期: ソフトターゲット 2026-06-30（2 ヶ月）
- 既存システム制約: なし（新規プロジェクト）
- 倫理: コードはオープンソース（MIT ライセンス想定、別途 Open Question 参照）

## Resolved Decisions（旧 Open Questions、2026-05-03 確定）
- [x] **D-01 (旧Q1)**: コメントは `shion <text>` で**行末まで**のみ。ブロックコメントは v1.0.0 では実装しない。
- [x] **D-02 (旧Q2)**: 文字列リテラルは**花名ペア** `bara_kuchi ... bara_tojiru` で囲む。`"..."` は使えない（全構文花名化原則の徹底）。
- [x] **D-03 (旧Q3)**: 数値は **数字表記 + 花数詞両対応**。`ichirin`(1) `futarin`(2) ... `nijuugorin`(25) のような花数詞も `25` と等価に解釈される。
- [x] **D-04 (旧Q4)**: ライセンスは **MIT**。
- [x] **D-05 (旧Q5)**: **演算子優先順位なし・全て左結合・括弧必須**。`expression ::= primary (binop primary)*` の単純規則のみ。`2 momo 3 marigold 4` は SyntaxError、`kobushi 2 momo 3 mokuren marigold 4` と必ず明示する。
- [x] **D-06 (旧Q6)**: 花言葉メッセージは**現代詩風**で統一。例: `※ 勿忘草の願い ─ この名前は記憶されていません`。
- [x] **D-07 (旧Q7)**: 季節モードは **二十四節気 (24 区分) + `toshi`（年中）= 25 区分**。
- [x] **D-08 (旧Q8)**: `floras kafun` 起動時、`FLORAS_SEED` 未設定なら自動的に `SEED=0` を設定（テスト再現性最優先）。
- [x] **D-09 (旧Q9)**: ホスティングは **Cloudflare Pages**。
- [x] **D-10 (旧Q10)**: ドメインは **`floras.dev` を取得**（年 ¥2,000 程度）。
- [x] **D-11 (旧Q11)**: 季節 allow-list は **独自シンプル表**（spec 内に明記）。歳時記準拠は採用しない。
- [x] **D-12 (旧Q12)**: `kareru` 世代カウンタは**評価ステップ数**で進む（決定論性最優先）。

## Glossary — Floras Token Map（**全トークン花名対応表**）

### Keywords / 制御構文
| Floras トークン | 役割 (一般言語) | 由来 |
|-----------------|----------------|------|
| `sakura` (桜) | 変数宣言 (`let`) | 始まりの花 |
| `yuri` (百合) | 関数定義 (`fn`) | 純粋・構造美 |
| `bara` (薔薇) | `if` | 選択の象徴（棘＝条件） |
| `tsubaki` (椿) | `else` | 落椿＝もうひとつの道 |
| `ume` (梅) | `while` | 寒中も咲き続ける＝反復 |
| `ran` (蘭) | `return` | 希少な実り |
| `himawari` (向日葵) | `import` | 太陽＝外部光源を取り込む |
| `shion` (紫苑) | コメント開始（行末まで） | 「忘れない」の花言葉＝注釈 |

### Literals / リテラル
| Floras トークン | 役割 |
|-----------------|------|
| `hasu` (蓮) | `true` |
| `asagao` (朝顔) | `false` |
| `tanpopo` (たんぽぽ) | `null` |

### Builtin Functions / 組み込み関数
| Floras トークン | 役割 |
|-----------------|------|
| `botan` (牡丹) | `print`（堂々たる出力） |
| `ayame` (菖蒲) | `input`（標準入力 1 行） |

### Brackets / 括弧（対）
| Open | Close | 役割 |
|------|-------|------|
| `kobushi` (辛夷) | `mokuren` (木蓮) | `(` `)` 関数呼び出し・グルーピング |
| `ajisai` (紫陽花) | `kikyou` (桔梗) | `{` `}` ブロック |
| `kosumosu` (コスモス) | `dahlia` (ダリア) | `[` `]` 配列（v0.2.0 予約） |

### Punctuation / 区切り記号
| Floras トークン | 役割 |
|-----------------|------|
| `nadeshiko` (撫子) | `;` 文末 |
| `kasumi` (霞草) | `,` 引数区切り |

### Assignment / 代入
| Floras トークン | 役割 |
|-----------------|------|
| `tsuyukusa` (露草) | `=` 代入（露が宿る＝値を宿す） |

### Comparison / 比較
| Floras トークン | 役割 |
|-----------------|------|
| `wasurenagusa` (勿忘草) | `==`（同じ記憶） |
| `azami` (薊) | `!=`（棘＝差異） |
| `fukujusou` (福寿草) | `<`（小さい・控えめ） |
| `tachiaoi` (立葵) | `>`（高く伸びる） |
| `suiren` (睡蓮) | `<=`（水面下含む） |
| `shobu` (菖蒲) | `>=`（凛として高い） |

### Arithmetic / 算術
| Floras トークン | 役割 |
|-----------------|------|
| `momo` (桃) | `+`（実りを足す） |
| `keitou` (鶏頭) | `-`（赤い切れ込み＝引く） |
| `marigold` (マリーゴールド) | `*`（無数の花弁＝掛ける） |
| `suzuran` (鈴蘭) | `/`（鈴のように分割） |
| `renge` (蓮華) | `%`（余りの花弁） |

### Logical / 論理
| Floras トークン | 役割 |
|-----------------|------|
| `sumire` (菫) | `&&` (and、寄り添う) |
| `pansy` (パンジー) | `\|\|` (or、どれかが咲く) |
| `keshi` (芥子) | `!` (not、反転の毒) |

> **凡例**: 上記のいずれかと衝突する識別子（変数名・関数名）は MUST 拒否される（FR-10）。
> **同名衝突解消**: `shobu`（菖蒲）と `ayame`（菖蒲）は同字異花。Floras 上は別トークンとして扱う（前者は比較演算子、後者は組み込み入力関数）。

### String Literal Pair / 文字列リテラルペア（D-02 で確定）
| Open | Close | 役割 |
|------|-------|------|
| `bara_kuchi` (薔薇口) | `bara_tojiru` (薔薇閉じる) | 文字列リテラル `"..."` の代替（**唯一の方法**） |

> 文字列内部の文字は花名ではなく**任意の Unicode テキスト**として扱う（Floras 識別子規則は適用されない）。`bara_kuchi` の直後から `bara_tojiru` の直前まで、そのままバイト列として取り込む。
> エスケープシーケンスは `bara_tojiru` を文字列内に含めたい場合のため `\bara_tojiru` を予約（v1.0.0 では未実装、含む文字列はパースエラー）。
> 例: `sakura name tsuyukusa bara_kuchi world bara_tojiru nadeshiko`

### Numeric Literal / 数値リテラル（D-03 で確定）
2 つの表記が等価:
1. **数字表記**: `25`, `3.14`, `-7` （標準）
2. **花数詞表記**: `nijuugorin` = 25, `ichirin` = 1, ... （等価、可読性スタイル）

#### 花数詞の生成規則（v0.5.0 まで段階導入）
基本パターン: **<日本語数読み> + `rin`**（一輪・二輪などの「輪」を `rin` で表す）

| 値 | 花数詞 | 値 | 花数詞 |
|---|---|---|---|
| 1 | `ichirin` | 11 | `juuichirin` |
| 2 | `nirin` | 12 | `juunirin` |
| 3 | `sanrin` | 20 | `nijuurin` |
| 4 | `yonrin` | 25 | `nijuugorin` |
| 5 | `gorin` | 50 | `gojuurin` |
| 6 | `rokurin` | 100 | `hyakurin` |
| 7 | `nanarin` | 1000 | `senrin` |
| 8 | `hachirin` | 10000 | `ichimanrin` |
| 9 | `kyuurin` | 0 | `mukarin` (無花輪) |
| 10 | `juurin` | 小数 | **数字表記のみ**（花数詞は整数限定） |

> v0.1.0 では数字表記のみ実装。花数詞 lexer は v0.5.0 で導入（季節モードと同じ波）。
> ネガティブ値は `keitou ichirin` （単項マイナス + 1） として扱う。

### Extended Keywords / 拡張キーワード（v0.2.0 以降）
| Floras トークン | 役割 | 導入 Ver | 由来 |
|-----------------|------|---------|------|
| `kakitsubata` (杜若) | 花占い演算子（非決定論的選択） | v0.3.0 | 「いずれが菖蒲か杜若」 |
| `kafun` (花粉) | テストブロック宣言 | v0.4.0 | 受粉＝検証 |
| `kareru` (枯れる) | 変数の明示解放 | v0.7.0 | 枯死＝ライフタイム終端 |
| `toshi` (年) | 季節宣言: 年中（制約なし、デフォルト） | v0.5.0 | 通年使用可 |

### 二十四節気宣言トークン（D-07 で確定、v0.5.0 で導入）
24 節気 + `toshi` の計 25 区分。各節気はおおよそ 15 日に対応。

| ID | トークン | 漢字 | 概日付（参考） | 親季節 |
|----|---------|------|--------------|--------|
| 1 | `risshun` | 立春 | 2/4 頃 | 春 |
| 2 | `usui` | 雨水 | 2/19 頃 | 春 |
| 3 | `keichitsu` | 啓蟄 | 3/5 頃 | 春 |
| 4 | `shunbun` | 春分 | 3/20 頃 | 春 |
| 5 | `seimei` | 清明 | 4/4 頃 | 春 |
| 6 | `kokuu` | 穀雨 | 4/19 頃 | 春 |
| 7 | `rikka` | 立夏 | 5/5 頃 | 夏 |
| 8 | `shouman` | 小満 | 5/20 頃 | 夏 |
| 9 | `boushu` | 芒種 | 6/5 頃 | 夏 |
| 10 | `geshi` | 夏至 | 6/21 頃 | 夏 |
| 11 | `shousho` | 小暑 | 7/7 頃 | 夏 |
| 12 | `taisho` | 大暑 | 7/22 頃 | 夏 |
| 13 | `risshuu` | 立秋 | 8/7 頃 | 秋 |
| 14 | `shosho` | 処暑 | 8/23 頃 | 秋 |
| 15 | `hakuro` | 白露 | 9/7 頃 | 秋 |
| 16 | `shuubun` | 秋分 | 9/22 頃 | 秋 |
| 17 | `kanro` | 寒露 | 10/8 頃 | 秋 |
| 18 | `soukou` | 霜降 | 10/23 頃 | 秋 |
| 19 | `rittou` | 立冬 | 11/7 頃 | 冬 |
| 20 | `shousetsu` | 小雪 | 11/22 頃 | 冬 |
| 21 | `taisetsu` | 大雪 | 12/7 頃 | 冬 |
| 22 | `touji` | 冬至 | 12/22 頃 | 冬 |
| 23 | `shoukan` | 小寒 | 1/5 頃 | 冬 |
| 24 | `daikan` | 大寒 | 1/20 頃 | 冬 |
| 25 | `toshi` | 年中 | （デフォルト） | - |

> 旧 `haru/natsu/aki/fuyu` トークンは**廃止**（D-07 採用に伴い）。代わりに 24 節気を直接宣言する。
> 季節 allow-list は「親季節の花トークン群 + その節気の代表花」で構成（次セクション）。

### Season Allow-Lists / 季節別の使用可花トークン（D-07 / D-11 で確定）

**ALWAYS_ALLOWED（全節気共通で使用可）**:
- 制御キーワード: `sakura, yuri, bara, tsubaki, ume, ran, himawari, shion, kakitsubata, kafun, kareru, botan, ayame, hasu, asagao, tanpopo`
- 全記号トークン: 括弧 (`kobushi/mokuren/ajisai/kikyou/kosumosu/dahlia`)・区切り (`nadeshiko/kasumi`)・代入 (`tsuyukusa`)・比較 (`wasurenagusa/azami/fukujusou/tachiaoi/suiren/shobu`)・算術 (`momo/keitou/marigold/suzuran/renge`)・論理 (`sumire/pansy/keshi`)
- 文字列ペア: `bara_kuchi/bara_tojiru`
- 季節宣言自身: 全 25 トークン
- 数値リテラル: 数字 + 全花数詞

**節気ごとの追加許可**: 以下の表で「**追加されるトークン**」のみが各節気で使える「装飾的な花」。それ以外の花トークンを使うと `FlorasSeasonError`。

| 節気 | 追加許可される装飾花トークン |
|------|--------------------------|
| `risshun` (立春) | tsubaki, ume |
| `usui` (雨水) | ume, suzuran |
| `keichitsu` (啓蟄) | mokuren, kobushi |
| `shunbun` (春分) | sakura, sumire |
| `seimei` (清明) | sakura, marigold |
| `kokuu` (穀雨) | botan, fuji |
| `rikka` (立夏) | yuri, ajisai |
| `shouman` (小満) | hasu, asagao |
| `boushu` (芒種) | ajisai, hanashoubu |
| `geshi` (夏至) | hasu, himawari |
| `shousho` (小暑) | himawari, keshi |
| `taisho` (大暑) | himawari, asagao |
| `risshuu` (立秋) | kikyou, hagi |
| `shosho` (処暑) | shion, hagi |
| `hakuro` (白露) | kosumosu, kasumi |
| `shuubun` (秋分) | higanbana, kiku |
| `kanro` (寒露) | kiku, kosumosu |
| `soukou` (霜降) | kiku, dahlia |
| `rittou` (立冬) | tsubaki, sazanka |
| `shousetsu` (小雪) | sazanka, suisen |
| `taisetsu` (大雪) | suisen, fukujusou |
| `touji` (冬至) | suisen, shobu |
| `shoukan` (小寒) | fukujusou, robai |
| `daikan` (大寒) | robai, tsubaki |
| `toshi` (年中) | **全花トークン許可（制約なし）** |

> **注**: 装飾的な花トークン（kiku/sakura/himawari 等）は「ALWAYS_ALLOWED に含まれず、特定節気でのみ使える」。例: `taisho` 宣言下では `kiku`（菊）はエラー、`himawari`（向日葵）は OK。
> 一部花名（`fuji`, `hanashoubu`, `hagi`, `higanbana`, `sazanka`, `suisen`, `robai`）は装飾用として新規予約（v0.5.0 で導入、評価動作は識別子と同じ）。

### Poesy Map / 花言葉エラーメッセージ（D-06 で確定: 現代詩風で統一）
| エラー型 | 花言葉行（提案） |
|---------|----------------|
| SyntaxError | `※ 椿の落ち際 ─ ここに想定外の音が混ざりました` |
| NameError | `※ 勿忘草の願い ─ この名前は記憶されていません` |
| TypeError | `※ 杜若の戸惑い ─ 似て非なる花を取り違えています` |
| ArityError | `※ 桜の花弁 ─ 数えてみると枚数が合いません` |
| RuntimeError | `※ 鶏頭の警鐘 ─ 実行の途中で枯れてしまいました` |
| InternalError | `※ 名もなき野花 ─ 言語自身の予期せぬ揺らぎです` |
| LifetimeError | `※ 萎みゆく花弁 ─ この変数はもう枯れています` |
| SeasonError | `※ 季節違いの開花 ─ いまは咲く時ではありません` |
