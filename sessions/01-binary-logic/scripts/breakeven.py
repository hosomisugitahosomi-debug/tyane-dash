"""損益分岐の判定。実測値を入れると合否が出る。

使い方
  python3 breakeven.py              早見表を全部出す
  python3 breakeven.py 12 1.5       平均値幅12pips・往復コスト1.5pipsで合否判定

モデル（RR 1:1・時間決済を想定）
  1トレードの期待値[pips] = (2p - 1) x G - C
    p = 勝率 / G = 平均値幅[pips] / C = 往復コスト[pips]
  損益分岐に必要な値幅  G_min  = C / (2p - 1)
  コスト込みの実効勝率   p_eff  = p - C / (2G)

前提（すべて仮定・未検証）
  バイナリーの1勝を +1R / 1敗を -1R に読み替え。ロジックの中身も実際の値幅も未使用。
"""
import sys

# (ペア, 実測勝率, 検証01の採用リスク%, 期間中のトレード数)
CASE = [
    ("ポン円",   0.643, 0.167, 353),
    ("ユロ円",   0.614, 0.150, 425),
    ("ビットドル", 0.583, 0.071, 1581),
    ("ドル円",   0.545, 0.115, 547),
]
TARGET = 12.0                    # 利益目標 %
COSTS = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
GAINS = [5, 10, 15, 20, 30]


def need_winrate(risk, trades):
    """利益目標に到達するのに必要な勝率。"""
    return (TARGET / risk / trades + 1) / 2


def verdict(gain, cost):
    """実測値を入れて合否を出す。"""
    print(f"=== 判定：平均値幅 {gain} pips / 往復コスト {cost} pips ===\n")
    print(f"{'ペア':<10}{'実測':>7}{'実効':>8}{'必要':>8}{'差':>8}   判定")
    for name, p, risk, trades in CASE:
        eff = p - cost / (2 * gain)
        need = need_winrate(risk, trades)
        gap = (eff - need) * 100
        mark = "合格" if gap >= 0 else "不合格"
        print(f"{name:<10}{p*100:>6.1f}%{eff*100:>7.1f}%{need*100:>7.1f}%{gap:>+7.1f}pt   {mark}")
    print("\n※RR 1:1の仮定にもとづく試算。実測のRRが違えば結果も変わる。")


def tables():
    print("=== 表A：損益分岐に必要な平均値幅 G_min [pips] ===")
    print("（これを下回ると期待値マイナス）")
    print(f"{'ペア':<10}" + "".join(f"{c:>7.1f}" for c in COSTS) + "  ← 往復コスト[pips]")
    for name, p, _, _ in CASE:
        edge = 2 * p - 1
        print(f"{name:<10}" + "".join(f"{c/edge:>7.1f}" for c in COSTS))

    print("\n=== 表B：コスト込みの実効勝率 p_eff [%] ===")
    print("（縦=平均値幅G / 横=往復コストC。50%を下回ると赤字）")
    for name, p, _, _ in CASE:
        print(f"\n  -- {name}（実測 {p*100:.1f}%）--")
        print("   G\\C  " + "".join(f"{c:>7.1f}" for c in [1.0, 2.0, 3.0, 5.0]))
        for g in GAINS:
            row = "".join(f"{(p - c/(2*g))*100:>7.1f}" for c in [1.0, 2.0, 3.0, 5.0])
            print(f"  {g:>3d}   {row}")

    print(f"\n=== 表C：利益目標{TARGET:.0f}%に必要な実効勝率 ===")
    print("（検証01の採用リスクとトレード数から逆算。期間は約5.5ヶ月）")
    for name, p, risk, trades in CASE:
        need = need_winrate(risk, trades)
        print(f"  {name:<10}実測 {p*100:4.1f}% → 必要 {need*100:4.1f}%（余裕 {(p-need)*100:+4.1f}pt）")

    print(f"\n=== 表D：利益目標{TARGET:.0f}%を維持できる最小の平均値幅 [pips] ===")
    print("（実質的な合格ライン。表Aより厳しい）")
    print(f"{'ペア':<10}" + "".join(f"{c:>7.1f}" for c in COSTS) + "  ← 往復コスト[pips]")
    for name, p, risk, trades in CASE:
        margin = p - need_winrate(risk, trades)
        if margin <= 0:
            print(f"{name:<10}" + "".join(f"{'不可':>7s}" for _ in COSTS))
        else:
            print(f"{name:<10}" + "".join(f"{c/(2*margin):>7.1f}" for c in COSTS))


if __name__ == "__main__":
    if len(sys.argv) == 3:
        verdict(float(sys.argv[1]), float(sys.argv[2]))
    elif len(sys.argv) == 1:
        tables()
    else:
        print(__doc__)
        sys.exit(1)
