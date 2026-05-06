# Floras

> すべての構文要素を花の名前で表現する、Python 製の小さなインタプリタ言語。

```floras
sakura name tsuyukusa bara_kuchi world bara_tojiru nadeshiko
yuri greet kobushi n mokuren ajisai
  botan kobushi kobushi bara_kuchi Hello,  bara_tojiru momo n mokuren mokuren nadeshiko
kikyou
greet kobushi name mokuren nadeshiko
```

```
$ floras run examples/hello.floras
Hello, world
```

## Why Floras

- **すべての構文要素が花**: キーワードだけでなく `(` `)` `{` `}` `;` `,` `==` `+` `*` まで全て花名で表現する。
- **学習価値**: Lexer / Parser / Tree-walking Evaluator の最小完動品を読みきれる規模で実装。
- **依存ゼロ**: Python 標準ライブラリのみで動く。

## Install

```bash
git clone https://github.com/yuuto22009911/floras.git
cd floras
pip install -e ".[dev]"
```

Python 3.11+ が必要。外部依存はゼロ（dev 環境のみ pytest / mypy / ruff）。

## Quickstart

```bash
floras run examples/hello.floras       # スクリプト実行
floras run examples/fizzbuzz.floras    # FizzBuzz
floras run examples/fib.floras         # フィボナッチ
floras repl                            # 対話モード
floras --version
floras run examples/hello.floras --ast # AST を JSON で表示
```

## Token Map（v0.1.0 Core）

### キーワード
| Floras | 役割 |
|--------|------|
| `sakura` | 変数宣言（let） |
| `yuri` | 関数定義（fn） |
| `bara` / `tsubaki` | if / else |
| `ume` | while |
| `ran` | return |
| `shion` | 行コメント |
| `hasu` / `asagao` / `tanpopo` | true / false / null |
| `botan` / `ayame` | print / input |

### 括弧
| Floras | 役割 |
|--------|------|
| `kobushi` / `mokuren` | `(` / `)` |
| `ajisai` / `kikyou` | `{` / `}` |
| `kosumosu` / `dahlia` | `[` / `]`（v0.2.0 予約） |

### 区切り・代入
| Floras | 役割 |
|--------|------|
| `nadeshiko` | `;` |
| `kasumi` | `,` |
| `tsuyukusa` | `=` |

### 比較
| Floras | 役割 |
|--------|------|
| `wasurenagusa` | `==` |
| `azami` | `!=` |
| `fukujusou` | `<` |
| `tachiaoi` | `>` |
| `suiren` | `<=` |
| `shobu` | `>=` |

### 算術
| Floras | 役割 |
|--------|------|
| `momo` | `+` |
| `keitou` | `-`（単項マイナスにも） |
| `marigold` | `*` |
| `suzuran` | `/` |
| `renge` | `%` |

### 論理
| Floras | 役割 |
|--------|------|
| `sumire` | `&&` |
| `pansy` | `\|\|` |
| `keshi` | `!` |

### 文字列リテラル
`bara_kuchi <任意テキスト> bara_tojiru` で囲む。例: `bara_kuchi Hello bara_tojiru`。

## 構文ルール（D-05: 演算子優先順位なし）

すべての二項演算子は同順位・左結合。**異なる演算子の混在には括弧 `kobushi ... mokuren` が必須**。

```floras
shion OK: 同一演算子の連続（左結合）
1 momo 2 momo 3 nadeshiko

shion OK: 括弧で混在
kobushi 1 momo 2 mokuren marigold 3 nadeshiko

shion NG: 括弧なしの混在 → SyntaxError
1 momo 2 marigold 3 nadeshiko
```

## サンプル

### Hello
```floras
sakura name tsuyukusa bara_kuchi world bara_tojiru nadeshiko
yuri greet kobushi n mokuren ajisai
  botan kobushi kobushi bara_kuchi Hello,  bara_tojiru momo n mokuren mokuren nadeshiko
kikyou
greet kobushi name mokuren nadeshiko
```

### FizzBuzz
[`examples/fizzbuzz.floras`](examples/fizzbuzz.floras) を参照。

### フィボナッチ
```floras
yuri fib kobushi n mokuren ajisai
  bara kobushi n fukujusou 2 mokuren ajisai
    ran n nadeshiko
  kikyou
  ran kobushi fib kobushi n keitou 1 mokuren mokuren momo fib kobushi n keitou 2 mokuren mokuren nadeshiko
kikyou
botan kobushi fib kobushi 10 mokuren mokuren nadeshiko
```

## エラー

```
Floras NameError at line 1: 'mystery' is not defined
Floras SyntaxError at line 3: expected nadeshiko but got kikyou
Floras ArityError at line 5: 'add' expects 2 args, got 1
Floras RuntimeError at line 7: division by zero
```

## ロードマップ

| Version | 機能 |
|---------|------|
| **v0.1.0**（現在） | Core 言語 + REPL |
| v0.2.0 | 花言葉エラー（Poesy） |
| v0.3.0 | `kakitsubata` 花占い演算子 |
| v0.4.0 | `kafun` テスト DSL |
| v0.5.0 | 季節モード（二十四節気） |
| v0.6.0 | `floras garden` AST 可視化 |
| v0.7.0 | `kareru` ライフタイム |
| v1.0.0 | Web プレイグラウンド |

詳細は `.claude/specs/language-core/` の requirements / design / tasks を参照。

## Development

```bash
pytest                # テスト実行
pytest --cov=floras   # カバレッジ
mypy floras tests     # 型チェック
ruff check .          # Lint
ruff format .         # フォーマット
```

## License

MIT
