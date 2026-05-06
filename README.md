# Floras Bloom

> 花を**宣言的に描いて束ね**、SVG / HTML / CSS に出力する、デザイナー向けの花テーマ DSL。

```bloom
bloom sakura {
  petals 5;
  size 240;
  color #FFB7C5;
  petal-curl 0.4;
  petal-notch 0.45;
  stamen-count 14;
  stamen-color #C44536;
  stroke #2C2825 width 1.2;
}
```

```bash
$ floras render sakura.bloom --out sakura.svg
```

→ Tailwind / shadcn / Squarespace / Figma 等にそのまま貼れる SVG が手に入る。

## なぜ Floras Bloom？

- **花は構造である**: 花弁数・反り・雄しべ・配置を pure data で宣言 → 拡大・縮小・色替え・量産が無料。
- **デザイナー語彙で書く**: `bloom` `palette` `bouquet` `scatter` — CSS / Tailwind の延長で読める命名。
- **出力は標準形式のみ**: SVG / HTML / CSS。独自フォーマットを作らず、Figma / Vercel / Tailwind とそのまま共存。

## Install

```bash
git clone https://github.com/yuuto22009911/floras.git
cd floras
pip install -e ".[dev]"
```

Python 3.11+ 必須。外部依存ゼロ（dev のみ pytest / mypy / ruff）。

## Quickstart

```bash
floras render examples/sakura.bloom --out sakura.svg     # ファイル出力
floras render examples/yuri.bloom                        # 標準出力
floras render examples/yuri.bloom --ast                  # AST を JSON で
floras --version
```

## v0.1.0 で書ける範囲

- **`bloom`** — 1 つの花の構造（花弁・雄しべ・茎・葉）を宣言
- **`palette`** — ブランド色を一括管理し、`brand.500` のドット記法で参照
- **`export`** — 出力先ファイルパスを宣言
- **色**: `#RRGGBB` / `oklch(L C H)` / `palette.token` / `palette.token tinted other.token 0.3`
- **数値**: `42` / `3.14` / `12px` / `50%` / `90deg` / `0.25turn`
- **配置パターン**: `arrange ring` (既定) / `arrange spiral` (黄金角)
- **コメント**: `shion 行末まで`

## サンプル 5 種

| ファイル | 花 | 特徴 |
|---------|-----|-----|
| [`examples/sakura.bloom`](examples/sakura.bloom) | 桜 | 5 弁・切れ込み付き |
| [`examples/bara.bloom`](examples/bara.bloom) | 薔薇 | 28 弁スパイラル・OKLCH 色 |
| [`examples/kiku.bloom`](examples/kiku.bloom) | 菊 | 24 弁・細長い花弁 |
| [`examples/cosmos.bloom`](examples/cosmos.bloom) | コスモス | 茎+葉つき |
| [`examples/yuri.bloom`](examples/yuri.bloom) | 百合 | palette 連携 |

## 構文ガイド

### 単一の花（最小例）
```bloom
bloom sakura {
  petals 5;
  size 200;
  color #FFB7C5;
}
```

### palette を使う
```bloom
palette monofloras {
  primary  oklch(0.85 0.07 80);
  ink      #2C2825;
  accent   #C77D4E;
}

bloom yuri {
  petals 6;
  color monofloras.primary;
  stroke monofloras.ink width 1.2;
}
```

### tinted で色を混ぜる
```bloom
palette b {
  rose   #FF0066;
  paper  #FFFFFF;
}
bloom soft_rose {
  color b.rose tinted b.paper 0.3;   shion ピンク寄りに 30% paper を混ぜる
}
```

## エラーメッセージ

```
Floras NameError at line 7: palette token 'brand.999' is not defined
Floras SyntaxError at line 3: expected ';' after bloom property
Floras ValidationError at line 12: 'petal-curl' must be in [0, 1]
```

## ロードマップ

| Version | 機能 |
|---------|------|
| **v0.1.0**（現在） | 単一 bloom + palette → SVG |
| v0.2.0 | palette トークンを export → CSS / Tailwind / JSON |
| v0.3.0 | bouquet（複数の花を 1 キャンバスに配置） |
| v0.4.0 | scatter（procedural 配置、要 seed） |
| v0.5.0 | motif（再利用可能パターン） |
| v0.6.0 | `floras preview <dir>` ライブリロードサーバ |
| v0.7.0 | tokens.css / tailwind 形式の export |
| v1.0.0 | Web プレイグラウンド |

詳細は `.claude/specs/bloom-dsl/` の requirements / design / tasks を参照。

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
