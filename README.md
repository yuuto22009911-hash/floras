# Floras Bloom

> 花を**宣言的に描いて束ね、散らす**、SVG / HTML / CSS に出力する**全構文日本語のデザイナー DSL**。

```bloom
※ 5 弁桜
色見本 春 {
  桜色 知覚色(0.85 0.10 12);
  墨   知覚色(0.20 0.02 30);
}

花 桜 {
  花弁数 5;
  大きさ 240;
  色 春.桜色;
  花弁反り 0.4;
  花弁切込 0.45;
  雄蕊数 14;
  輪郭 春.墨 幅 1.2;
}
```

```bash
$ floras render examples/桜.bloom --out 桜.svg
```

→ Tailwind / shadcn / Squarespace / Figma にそのまま貼れる SVG。

## 言語の特徴

- **アルファベットを 1 文字も使わない**: キーワード・識別子・色・単位すべて日本語。文字列リテラル内のファイルパスのみデータとして例外。
- **花は構造である**: `花弁数` `花弁反り` `雄蕊数` `茎` を pure data で宣言 → 拡大・縮小・色替え・量産が無料。
- **手描き感を量産**: `散らす` で procedural 配置（要 `種`）。同じ `.bloom` は bit-identical な SVG を出す。
- **依存ゼロ**: Python 標準ライブラリのみ。

## Install

```bash
git clone https://github.com/yuuto22009911/floras.git
cd floras
pip install -e ".[dev]"
```

Python 3.11+ 必須。外部依存ゼロ（dev のみ pytest / mypy / ruff）。

## ブラウザで試す

`playground/index.html` を開けば、インストール不要で Floras Bloom が動きます（Pyodide でブラウザだけで Python を動かしています）。

```bash
python -m http.server 7879 --directory playground
# → http://localhost:7879/
```

## Quickstart

```bash
floras render examples/さくら.bloom --out さくら.svg          # ファイル出力
floras render examples/桜吹雪.bloom                          # 標準出力
floras render examples/桜吹雪.bloom --ast                    # AST を JSON で
floras preview examples/                                    # ライブリロード
floras tokens examples/ヒーロー.bloom --format tailwind      # 色見本 → CSS
floras --version
```

`floras preview` は `examples/` 配下の全 `.bloom` をブラウザに並べて表示し、
ファイルを保存するたびに該当 SVG だけが SSE 経由で差し替わります（フルリロード
不要、~1 秒以内）。`http://127.0.0.1:7878` を開くだけ。

## 言語仕様（〜 v0.4.0）

### トップレベル宣言
| Floras | 役割 |
|---|---|
| `色見本 名前 { ... }` | パレット（ブランド色を一括管理） |
| `花 名前 { ... }` | 単一の花の構造定義 |
| `模様 名前 { ... }` | 「花 + 蕾 + 葉」など複数要素を 1 単位として再利用 |
| `花束 名前 { ... }` | 複数の花 / 模様を 1 キャンバスに構成 |
| `書出 対象 へ "path";` | 出力先指定 |

### 花のプロパティ
| Floras | 意味 | 例 |
|---|---|---|
| `花弁数` | 花弁の数 | `花弁数 5;` |
| `花弁幅` / `花弁丈` | 花弁の幅 / 丈 | `花弁幅 28;` |
| `花弁反り` | ふくらみ 0..1 | `花弁反り 0.4;` |
| `花弁切込` | 先端の切れ込み 0..1（桜の特徴） | `花弁切込 0.45;` |
| `雄蕊数` / `雄蕊半径` / `雄蕊色` | 雄しべ | `雄蕊数 12;` |
| `茎` / `茎丈` / `茎色` | 茎を生やす（真/偽） | `茎 真; 茎丈 200;` |
| `葉数` | 葉の枚数 | `葉数 4;` |
| `並び` | `輪`(既定) または `螺旋`(黄金角) | `並び 螺旋;` |
| `大きさ` / `回転` / `色` | 全体の寸法・回転・色 | `大きさ 240;` |
| `輪郭 色 幅 N;` | 線（色 + 太さ） | `輪郭 春.墨 幅 1.2;` |

### 花束のプロパティ
| Floras | 役割 |
|---|---|
| `画布 W × H;` | キャンバスサイズ（必須・先頭） |
| `背景 色;` | 全面背景 |
| `置く 花名 に 中央;` | 中央配置 |
| `置く 花名 に (x, y);` | 座標指定 |
| `置く 花名 に 中央 { 大きさ N; 色 ...; };` | 配置時オーバーライド |
| `散らす { 元 花名; 数 N; 領域 ...; 種 N; }` | procedural 配置 |

### 散らす(scatter) の領域
| Floras | 意味 |
|---|---|
| `領域 画布;` | キャンバス全面に一様分布 |
| `領域 輪 中央 (cx, cy) 内 r1 外 r2;` | リング内 |
| `領域 矩形 (x1, y1) へ (x2, y2);` | 矩形内 |
| `領域 格子 列 N 行 M;` | N×M グリッド（決定論的） |

### 数値・色リテラル
| 種類 | 例 |
|---|---|
| 整数 / 小数 | `42` `3.14` |
| 単位付き数値 | `12点` (px) `50%` `90度` `0.25周` |
| 範囲（散らす内のみ） | `12..32` |
| 知覚色（OKLCH） | `知覚色(0.85 0.10 12)` |
| パレット参照 | `春.桜色` |
| 混色 | `春.桜色 混ぜ 春.紙 0.4` |

### 定数とコメント
| Floras | 意味 |
|---|---|
| `中央` | キャンバス中心 |
| `自動` | grid 領域で N×M に合わせる |
| `乱数` | 散らす内で seed 由来の乱数値 |
| `真` / `偽` / `無` | bool / null |
| `※ ...` (行末まで) | コメント |

## サンプル一覧

| ファイル | 内容 |
|---|---|
| [`examples/さくら.bloom`](examples/さくら.bloom) | 5 弁・切れ込み付きのさくら |
| [`examples/ばら.bloom`](examples/ばら.bloom) | 28 弁螺旋のばら / 知覚色 |
| [`examples/きく.bloom`](examples/きく.bloom) | 24 弁の細長いきく |
| [`examples/こすもす.bloom`](examples/こすもす.bloom) | 茎+葉つきのこすもす |
| [`examples/ゆり.bloom`](examples/ゆり.bloom) | 色見本連携のゆり |
| [`examples/ヒーロー.bloom`](examples/ヒーロー.bloom) | 1200×630 花束 |
| [`examples/桜吹雪.bloom`](examples/桜吹雪.bloom) | **散らす** で桜吹雪を演出 |
| [`examples/枝.bloom`](examples/枝.bloom) | **模様** で「さくら+蕾」を 8 枝散布 |

`python docs/build_gallery.py` で `docs/gallery.html` を生成すると、全サンプルと出力 SVG とソースコードを 1 ページで確認できます。

## フロントエンド統合 (`floras tokens`)

`色見本` 宣言を 3 種類のフォーマットで書き出し、React/Tailwind プロジェクトから即参照できます。

```bash
floras tokens examples/ヒーロー.bloom --format css      --out tokens.css
floras tokens examples/ヒーロー.bloom --format tailwind --out theme.css
floras tokens examples/ヒーロー.bloom --format json     --out tokens.json
```

出力例（CSS, Tailwind v4 互換）:
```css
@theme {
  --color-春-桜色: #FFB3BC;
  --color-春-紙:   #F9F4EE;
  --color-春-墨:   #231715;
}
```

→ React で `<div className="bg-春-桜色">` のように Japanese 識別子のままクラス名で参照可能（モダンブラウザは CSS Custom Property に CJK を許容）。

## エラー

```
Floras NameError at line 7: palette token '春.見つからない' is not defined
Floras SyntaxError at line 3: expected ';' after bloom property
Floras ValidationError at line 12: '花弁反り' must be in [0, 1]
Floras SyntaxError at line 5: scatter requires '種 <integer>;' for determinism
```

## ロードマップ

| Version | 機能 |
|---|---|
| v0.1.0 | 単一 花 + 色見本 → SVG |
| v0.3.0 | 花束（複数の花を 1 キャンバスに配置） |
| v0.4.0 | 散らす（procedural 配置）+ 全構文日本語化 |
| v0.5.0 | 模様（再利用可能パターン）+ 花名ひらがな化 + 負数座標 |
| v0.6.0 | `floras preview` ライブリロードサーバ |
| v0.7.0 | `floras tokens` で 色見本 を CSS / Tailwind / JSON へ書き出し |
| **v1.0.0**（現在） | **Web プレイグラウンド（Pyodide でブラウザだけで実行）** |
| v0.7.0 | 色見本 → CSS / Tailwind / JSON 書出 |
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
