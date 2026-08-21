# tyane-dash

TyanePon 勝率ダッシュボード。

## ファイル構成

| ファイル | 中身 | 誰が触るか |
|---|---|---|
| `index.html` | 見た目（HTML + CSS）だけ | デザイン変更のとき |
| `data.js` | 成績データ `var D = {...}` | Colab / 更新.bat が自動生成 |
| `logic.js` | 計算ロジック（DOMに触らない純粋関数） | **ロジック改修はここ** |
| `app.js` | 画面描画 | 表示項目を増やすとき |

`logic.js` は `<script>` からも Node からも読めるので、ブラウザと検証スクリプトで
**同じ計算コード**を使えます。

## 動かし方

`index.html` をブラウザで開くだけ（サーバー不要）。
4ファイルは同じフォルダに置いてください。

## データ更新

`data.js` の1行（`var D = {...};`）を丸ごと置き換えるだけ。
`index.html` は触らなくてよくなったので、データ更新とロジック改修が衝突しません。

## スマホから作業する

GitHub Pages で公開すると `https://<ユーザー名>.github.io/tyane-dash/` で成績が見られます。

有効化: リポジトリの **Settings → Pages → Source: Deploy from a branch → main / (root)** → Save

## ロジックの検証

```
node -e 'const L=require("./logic.js"); ...'
```
