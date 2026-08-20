# あなたがやること

## ① FAQのページを開いてコピペする（5分・今すぐできる）
https://faq.fundedelite.com/en/articles/12675454-tradable-instruments-and-commissions

**GBPJPY / EURJPY / BTCUSD** のスプレッドと手数料を見る（`.c` 付きの銘柄）。
本文をコピペしてもらえれば、そのまま損益分岐の計算に入れる。

## ② サポートに1問だけ聞く（購入前でOK）
公式サイト右下のライブチャット、または https://fundedelite.com/contact

> ダッシュボードに表示される「スキャルピング上限額（scalp limit）」は
> どのように決まりますか？ 具体的な金額または算出方法を教えてください。

回答は `docs/questions-to-fundedelite.md` の記入欄に貼る。**スクショも残すこと。**

## ③ ローカルのClaude Codeで検証を始める（本番）
MT4/MT5が入っているPCで：

```
git clone https://github.com/hosomisugitahosomi-debug/tyane-dash.git
cd tyane-dash
git checkout claude/aiajan-usability-t2w38v
```

そのフォルダでClaude Codeを起動して、これを投げるだけ：

```
HANDOFF.md を読んで続きから始めて
```

**測るのは1つだけ：エントリーから3分後の平均値幅（pips）。**

---

## 優先順位
①が一番早く終わり、効果も大きい（②の回答待ちの間に③を進められる）。
③は時間がかかるので、①②と並行して始めてよい。
