"""損益分岐スプレッドの早見表。ローカルで平均値幅が出たら当てはめるだけで合否が分かる。

モデル（RR 1:1・時間決済を想定）
  1トレードの期待値[pips] = (2p - 1) x G - C
    p = 勝率, G = 1トレードあたりの平均値幅[pips], C = 往復コスト[pips]（スプレッド+スリッページ+手数料）
  損益分岐に必要な値幅  G_min = C / (2p - 1)
  コスト込みの実効勝率   p_eff = p - C / (2G)   ← 検証01の表にそのまま入れられる
"""
WR = {"ポン円": 0.643, "ユロ円": 0.614, "ビットドル": 0.583, "ドル円": 0.545}
COSTS = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
GAINS = [5, 10, 15, 20, 30]

print("=== 表A：損益分岐に必要な平均値幅 G_min [pips] ===")
print("（実測勝率のまま。この値幅を取れなければ期待値マイナス）")
print("ペア        " + "".join(f"{c:>7.1f}" for c in COSTS) + "  ← 往復コスト[pips]")
for name, p in WR.items():
    edge = 2 * p - 1
    print(f"{name:10s}" + "".join(f"{c/edge:>7.1f}" for c in COSTS))

print("\n=== 表B：コスト込みの実効勝率 p_eff [%] ===")
print("（縦=平均値幅G[pips] / 横=往復コストC[pips]。分岐点50%を下回ると赤字）")
for name, p in WR.items():
    print(f"\n  -- {name}（実測 {p*100:.1f}%）--")
    print("   G\\C  " + "".join(f"{c:>7.1f}" for c in [1.0, 2.0, 3.0, 5.0]))
    for g in GAINS:
        row = "".join(f"{(p - c/(2*g))*100:>7.1f}" for c in [1.0, 2.0, 3.0, 5.0])
        print(f"  {g:>3d}   {row}")

print("\n=== 表C：利益目標12%に到達するのに必要な実効勝率 ===")
print("（検証01の採用リスクとトレード数から逆算。期間は約5.5ヶ月）")
# (ペア, 検証01の採用リスク%, 期間中のトレード数)
CASE = [("ポン円", 0.167, 353), ("ユロ円", 0.150, 425), ("ビットドル", 0.071, 1581), ("ドル円", 0.115, 547)]
for name, r, n in CASE:
    need_R = 12.0 / r                 # 利益目標12%に必要なR数
    need_p = (need_R / n + 1) / 2     # そのR数を出すのに必要な勝率
    print(f"  {name:10s} 実測 {WR[name]*100:4.1f}% → 必要 {need_p*100:4.1f}%"
          f"（余裕 {(WR[name]-need_p)*100:+4.1f}pt）")
print("  ※必要勝率を p_eff が下回ると、5.5ヶ月では利益目標12%に届かない")

print("\n=== 表D：利益目標12%を維持できる最小の平均値幅 [pips] ===")
print("（表Cの余裕を使い切るまで許容。G_min = C / (2 x 余裕)）")
print("ペア        " + "".join(f"{c:>7.1f}" for c in COSTS) + "  ← 往復コスト[pips]")
for name, r, n in CASE:
    need_p = (12.0 / r / n + 1) / 2
    margin = WR[name] - need_p
    if margin <= 0:
        print(f"{name:10s}" + "".join(f"{'不可':>7s}" for _ in COSTS))
    else:
        print(f"{name:10s}" + "".join(f"{c/(2*margin):>7.1f}" for c in COSTS))
