# ローカル実行への移行手順

TICKデータとMQLソースはローカルPCにあるため、検証はローカルのClaude Codeで行う。

## 1. インストール
- Claude Code デスクトップアプリ（Mac / Windows）または CLI を入れる
- MT4/MT5 が入っているPCで実行すること

## 2. リポジトリを取得
```
git clone https://github.com/hosomisugitahosomi-debug/tyane-dash.git
cd tyane-dash
git checkout claude/aiajan-usability-t2w38v
```

## 3. Claude Code をそのフォルダで起動
ルートの `CLAUDE.md` が自動で読まれるので、作業ルールの説明は不要。

## 4. 最初に投げるプロンプト（コピペ用）
```
sessions/01-binary-logic/ を読んで、続きから始めて。
まず以下2つの場所を特定してほしい：
1. MQLのEAソース（.mq4 / .mq5）
2. TICKデータ

見つけたら、ファイル一覧とサイズだけ報告して。中身はまだ読まなくていい。
```

## 5. 探す場所の目安（Windows）
- MT5: `C:\Users\<ユーザー名>\AppData\Roaming\MetaQuotes\Terminal\<英数字>\MQL5\Experts\`
- MT4: 同上の `MQL4\Experts\`
- MT5のTICK: `...\Terminal\<英数字>\Bases\<業者名>\ticks\`（**独自バイナリ形式。そのままでは解析不可**）
- CSVでエクスポート済みのデータがあればそちらを優先

## 注意
- `.gitignore` で大容量データ（csv / hst / fxt / tkc / zip / data/）はコミット対象外にしてある
- リポジトリに上げるのは **MQLソース** と **集計結果** のみ
