# Floras — Project Steering

> プロジェクト全体に適用される不変ルール。全 Spec が本書を参照する。

## Vision
**Floras** は、すべての構文要素（キーワード・括弧・演算子・記号）が**花の名前**で構成される、Python 製の小さなインタプリタ言語である。読むと花畑を歩いているような体験を提供しつつ、言語処理系の基本構造（Lexer / Parser / Evaluator）を学習・展示できる作品とする。

## Tech Stack
- **実装ホスト言語**: Python 3.11+
- **依存**: 標準ライブラリのみ（外部ライブラリ原則ゼロ）
- **テスト**: `pytest`
- **型**: `mypy --strict`
- **Lint/Format**: `ruff` (lint + format 統合)
- **配布**: `pyproject.toml` (PEP 621) / `pip install -e .` でローカル実行
- **CI**: GitHub Actions (test + mypy + ruff)
- **REPL**: 標準 `code.InteractiveConsole` ベース

## Code Style
```python
# 良い例: 型を明示し、純粋関数を主体に
from dataclasses import dataclass

@dataclass(frozen=True)
class Token:
    kind: str
    lexeme: str
    line: int

def tokenize(source: str) -> list[Token]:
    ...
```
- すべての public 関数は型注釈必須
- イミュータブル優先（`@dataclass(frozen=True)` / `tuple` / `Mapping`）
- 早期 return（else を避ける）
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
| run script | `floras run examples/hello.floras` |
| repl | `floras repl` |
| build (sdist/wheel) | `python -m build` |

## Project Layout
```
floras/
├── floras/                  # Python package
│   ├── __init__.py
│   ├── tokens.py            # TokenKind / Token
│   ├── lexer.py             # source → Token[]
│   ├── ast_nodes.py         # AST ノード定義
│   ├── parser.py            # Token[] → AST
│   ├── environment.py       # スコープ管理
│   ├── evaluator.py         # AST 評価
│   ├── errors.py            # 例外型
│   ├── repl.py              # 対話モード
│   └── cli.py               # エントリーポイント
├── tests/
│   ├── test_lexer.py
│   ├── test_parser.py
│   ├── test_evaluator.py
│   └── fixtures/            # .floras サンプル
├── examples/
│   ├── hello.floras
│   ├── fizzbuzz.floras
│   └── fib.floras
├── docs/
│   └── language-reference.md
├── pyproject.toml
├── README.md
└── .claude/                 # Spec & Steering（本書含む）
```

## Naming Convention
- Python モジュール: `snake_case.py`
- Python クラス: `PascalCase`
- Floras キーワード: 全て**花の日本語ローマ字名**（例: `sakura`, `bara`, `kobushi`）
- Floras 識別子: ユーザー任意（花以外も可、ただし慣例として花を推奨）
- ファイル拡張子: `.floras`

## Testing
- **配置**: `tests/test_<module>.py`（実装と並列）
- **粒度**: lexer/parser/evaluator それぞれ独立にユニットテスト
- **End-to-End**: `examples/*.floras` を実行して期待出力と比較
- **カバレッジ**: 主要ロジック 85% 以上
- **必須**: 新トークン・新構文を追加したらテストも同時に追加

## Git Workflow
- **ブランチ**: `feature/<spec-slug>`, `fix/<issue>`
- **コミット**: Conventional Commits (`feat`, `fix`, `refactor`, `test`, `docs`, `chore`)
- **コミット粒度**: Lexer / Parser / Evaluator は機能単位で別コミット
- **PR**: 1 機能 = 1 PR、tasks.md のチェックリストを本文に転記
- **マージ前**: `pytest && mypy && ruff check` を全パス必須

## Boundaries (Always / Ask first / Never)

### Always
- 型注釈を全 public 関数に付与
- 新キーワード追加時は `requirements.md` のトークン表も更新
- pytest を通してから commit
- Floras エラーメッセージは「行番号 + 該当トークン + 期待値」を必ず含める

### Ask first（人間確認必須）
- 外部ライブラリの追加（標準ライブラリ縛りを破る場合）
- 文法の breaking change（既存 .floras スクリプトが動かなくなる変更）
- 新キーワードの花名割り当て（命名は作品性に直結するため）

### Never
- `eval()` / `exec()` で Floras を実装すること（学習目的を破壊）
- ホスト Python のスタックトレースをユーザーに直接見せる（Floras 用エラーで包む）
- main / master への force push
- テストなしで Lexer/Parser/Evaluator を変更

## Constraints / Conventions
- すべての構文要素を花の名前にする原則は**絶対**（記号・括弧・演算子も含む）
- 数値リテラル（0-9, .）と文字列リテラル（"..."）のみ非花トークン
- コメントは `shion ...` で行末まで（`shion` = 紫苑）
- インデントは意味を持たない（ブロックは `ajisai` ... `kikyou` で囲む）

## Versioning
- SemVer 準拠
- v0.1.0: FizzBuzz が動く最小構成（本 spec の到達点）
- v0.2.0+: 配列・高階関数・REPL 拡張など別 spec で扱う
