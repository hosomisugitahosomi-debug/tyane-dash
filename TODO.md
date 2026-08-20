# あなたがやること

## ① 購入画面をコピペする（3分・今すぐできる）
https://app.fundedelite.jp/website/choose-plan

LITE・インスタントの価格が分かれば、パターン別の総額表を作る。

## ② サポートの返答を待つ（送信済み）
GBPJPYc / EURJPYc / BTCUSD のスプレッドと、FX手数料$3の適用範囲。
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

**測るのは1つ：決済3分20秒時点の平均獲得値幅（pips）。**

## ④（任意）フラッシュ$25,000口座を約700円で買う
- 失敗しても700円。ロジックの実地テストとして最安
- **スプレッドを自分で実測できる**（②の回答を待たずに済む）
- 通れば$159（約24,000円）を払って本番

---

## 優先順位
③が本番。①は3分で終わるので先に済ませる。②は待つだけ。
④はスプレッドを早く確定させたい場合の近道。
