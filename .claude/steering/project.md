# Floras — Project Steering

> プロジェクト全体に適用される不変ルール。全 Spec が本書を参照する。

## Vision
**Floras** は、花を宣言的に描いて束ね、**SVG / HTML / CSS** に出力する、デザイナー向けの花テーマ DSL である。
ヒーローセクション、ブランド装飾、ロゴ、パターン背景など、Web デザイン現場で「花の絵」を必要とする場面で、Tailwind の color token のような感覚で「花の構造そのもの」をコードで宣言できる。

### コンセプト 3 軸
1. **花は構造である**: 花弁数・反り・雄しべ・配置を pure data で宣言する → 同じ宣言から拡大・縮小・色替え・量産が無料。
2. **デザイナー語彙で書く**: 「`bloom sakura`」「`scatter petals`」「`bouquet hero`」など、CSS や Figma の延長で読める命名。プログラミングが目的ではない。
3. **出力は標準形式のみ**: SVG / HTML / CSS。独自フォーマットを作らない。Figma / Vercel / Squarespace / Tailwind とそのまま共存する。

### 旧方針との関係
旧 spec [`.claude/specs/language-core/`](../specs/language-core/) は「花名で全構文を表現する Tree-walking Interpreter」を v0.1.0 まで実装したが、**「デザイナー言語」へ方針転換した** (2026-05-07)。Lexer / Parser インフラの一部は本 DSL でも再利用するが、ターゲット領域は完全に新規。

## Tech Stack
- **実装ホスト言語**: Python 3.11+
- **依存**: Python 標準ライブラリのみ（外部依存ゼロ）
- **テスト**: `pytest`
- **型**: `mypy --strict`
- **Lint/Format**: `ruff` (lint + format 統合)
- **配布**: `pyproject.toml` (PEP 621) / `pip install -e .`
- **CI**: GitHub Actions (test + mypy + ruff)
- **出力フォーマット**: SVG (主軸) / HTML (preview) / CSS (custom properties)
- **プレビュー**: 標準ライブラリ `http.server` ベースのライブリロード（v0.6.0 以降）

## Code Style
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Petal:
    width: float
    height: float
    curl: float
    notch: float = 0.0

def render_petal(p: Petal) -> str:
    """Return an SVG <path> string for one petal."""
    ...
```
- 全 public 関数に型注釈必須
- イミュータブル優先（`@dataclass(frozen=True)` / `tuple` / `Mapping`）
- 早期 return（`else` を避ける）
- マジックナンバー禁止（モジュール定数化）
- コメントは WHY のみ。WHAT は命名で表現

## Commands
| 用途 | コマンド |
|------|---------|
| install (dev) | `pip install -e ".[dev]"` |
| test | `pytest` |
| typecheck | `mypy floras tests` |
| lint | `ruff check .` |
| format | `ruff format .` |
| 1 ファイルを SVG に変換 | `floras render examples/sakura.bloom --out sakura.svg` |
| プレビューサーバ起動 (v0.6.0+) | `floras preview examples/` |
| パレットを CSS 変数に書き出す (v0.7.0+) | `floras tokens examples/brand.bloom --out tokens.css` |

## Project Layout
```
floras/
├── floras/
│   ├── __init__.py
│   ├── tokens.py            # TokenKind / Token (新キーワードで再構築)
│   ├── lexer.py             # source → Token[]
│   ├── ast_nodes.py         # AST 定義（Bloom / Bouquet / Scatter / ...）
│   ├── parser.py            # Token[] → AST
│   ├── geometry/            # 幾何形状の生成器
│   │   ├── petal.py         # 花弁 SVG path
│   │   ├── stamen.py        # 雄しべ
│   │   └── leaf.py          # 葉
│   ├── compose/             # AST → SceneGraph 変換
│   │   ├── resolver.py      # シンボル解決（palette / bloom 参照）
│   │   ├── scatter.py       # procedural 配置
│   │   └── scene.py         # SceneGraph 中間表現
│   ├── render/              # SceneGraph → 出力
│   │   ├── svg.py
│   │   ├── html.py
│   │   └── css.py
│   ├── preview.py           # ローカル HTTP サーバ (v0.6.0)
│   ├── errors.py
│   └── cli.py
├── tests/
├── examples/
│   ├── sakura.bloom
│   ├── hero.bloom
│   └── brand-tokens.bloom
├── docs/
├── pyproject.toml
└── README.md
```

## Naming Convention
- Python モジュール: `snake_case.py`
- Python クラス: `PascalCase`
- Floras DSL のソース拡張子: `.bloom`
- Floras DSL キーワード: 英単語 + 花テーマで意味が直感的に通るもの（`bloom` `bouquet` `scatter` `palette` `motif` `canvas` `place` `export`）
- Floras DSL 識別子: `[a-zA-Z_][a-zA-Z0-9_-]*`（ハイフン許可、kebab-case 慣例）

## Testing
- **配置**: `tests/test_<module>.py`（実装と並列）
- **粒度**: lexer / parser / geometry / compose / render それぞれ独立にユニットテスト
- **Snapshot**: SVG 出力は固定 fixture と diff（座標は小数点 2 桁丸め）
- **End-to-End**: `examples/*.bloom` をすべて render して期待 SVG と比較
- **Visual**: 主要 fixture を `docs/gallery.html` に並べ、CI で Playwright スクリーンショット差分（v1.0.0+ で追加）
- **カバレッジ**: 主要ロジック 85% 以上

## Git Workflow
- **ブランチ**: `feature/<spec-slug>`, `fix/<issue>`
- **コミット**: Conventional Commits (`feat`, `fix`, `refactor`, `test`, `docs`, `chore`)
- **コミット粒度**: lexer / parser / geometry / render は機能単位で別コミット
- **PR**: 1 機能 = 1 PR、tasks.md のチェックリストを本文に転記
- **マージ前**: `pytest && mypy && ruff check` 全パス必須

## Boundaries (Always / Ask first / Never)

### Always
- 型注釈を全 public 関数に付与
- 新 DSL キーワード追加時は `requirements.md` の Glossary も更新
- pytest を通してから commit
- SVG 出力は座標小数点 2 桁丸め（snapshot 安定性）
- 出力 SVG は `viewBox` 必須（レスポンシブ前提）

### Ask first（人間確認必須）
- 外部ライブラリの追加（標準ライブラリ縛りを破る場合）
- 新 DSL キーワードの追加（語彙はデザイナー学習コストに直結）
- 文法の breaking change（既存 `.bloom` ファイルが render 不可になる変更）
- 出力 SVG の構造変更（既存ユーザーの DOM 依存に影響）

### Never
- 出力に PNG / JPG / 動画形式を加える（v0.1.0 スコープ外、外部ツールで変換）
- ランダム要素を seed なしで使う（同じ `.bloom` は同じ SVG を出すべき）
- ホスト Python のスタックトレースをユーザーに直接見せる（Floras 用エラーで包む）
- main / master への force push
- テストなしで Lexer / Parser / Renderer を変更

## Constraints / Conventions
- 新 DSL は **宣言的**: 制御構文（if / while）は v0.1.0 では持たない。デザインに必要な「分岐」は palette と複数 bouquet で表現する。
- 数値リテラル: 整数 / 小数 / `12px` / `50%` / `0..1` (range) / `random` / `auto`
- カラー: `#RRGGBB` / `oklch(L C H)` / `palette.token` 参照（`brand.500` のようなドット記法）
- 座標系: SVG 標準（左上 0,0、Y 下向き）。`at center` のようなショートカットも提供
- 単位: `px` 既定、`%` は親要素相対、`vw/vh` は canvas 相対
- 角度: 度数法 (`deg`)、`turn`（1 turn = 360deg）も許容
- すべての乱数は `seed` 必須（決定論性）

## Versioning
- SemVer 準拠
- v0.1.0: 単一 bloom → SVG（最小完動品）
- v0.2.0: palette トークン
- v0.3.0: bouquet（複数の bloom を構成）
- v0.4.0: scatter（procedural 配置）
- v0.5.0: motif（再利用可能パターン）
- v0.6.0: HTML preview + ライブリロード
- v0.7.0: CSS export
- v1.0.0: Web プレイグラウンド
