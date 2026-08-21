---
description: 実測値を入れて FundedElite の合否を判定する
argument-hint: 平均値幅[pips] 往復コスト[pips]（例: 12 1.5）
---
`sessions/01-binary-logic/scripts/breakeven.py` を実行してください。

引数: $ARGUMENTS
（平均値幅[pips] と 往復コスト[pips]。指定がなければ引数なしで実行し、表全体を出す）

```
python3 sessions/01-binary-logic/scripts/breakeven.py $ARGUMENTS
```

出力の解釈は **3点だけ**、簡潔に報告してください：
1. ペアごとの実効勝率 p_eff
2. 必要勝率との差
3. 合否

判定式： `p_eff = 実測勝率 - 往復コスト ÷ (2 × 平均値幅)`
