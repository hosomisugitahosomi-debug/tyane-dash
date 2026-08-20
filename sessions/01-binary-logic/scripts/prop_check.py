"""手元の勝敗データを FundedElite のルールに当てて合否を見る。

仮定（すべて未検証。数値の解釈時は必ずこれを添えること）
  A1. バイナリーの1勝= +1R / 1敗= -1R（RR 1:1）に読み替える
  A2. 日内のトレード順序が不明なため、DDは「日次終値ベース」。日中DDは過小評価される
  A3. Daily Loss Limit = 3%（記事のInstantプランの値。他プランは未確認）
  A4. スプレッド・スリッページは未考慮（FXコストを引く前の上限値）
"""
import json, pathlib

DL = 3.0          # Daily Loss Limit %
CAP = DL / 2      # 同一銘柄の1日リスク上限 = Daily Loss Limit の50%
MAXDD = 10.0      # 最大DD %
TARGET = 12.0     # 利益目標 %
CONSIST = 30.0    # 一貫性ルール %

d = json.loads((pathlib.Path(__file__).parent / "data.json").read_text(encoding="utf-8"))
pairs = d["pairs"]


def series(daily):
    """日付順に (日付, トレード数, 純損益R) を返す。"""
    return [(k, v["w"] + v["l"], v["w"] - v["l"]) for k, v in sorted(daily.items())]


def max_dd_r(rows):
    """日次終値ベースの最大DD（R単位）。"""
    cum = peak = dd = 0.0
    for _, _, net in rows:
        cum += net
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    return dd


def report(name, rows):
    n_days = len(rows)
    n_trades = sum(n for _, n, _ in rows)
    total_r = sum(net for _, _, net in rows)
    wr = (n_trades + total_r) / 2 / n_trades * 100
    dd = max_dd_r(rows)
    max_n = max(n for _, n, _ in rows)

    # 1トレードあたりリスク r% の上限
    r_dd = MAXDD / dd if dd else float("inf")      # DD制限から
    r_cap = CAP / max_n                            # 同一銘柄リスク制限から
    r = min(r_dd, r_cap)

    # 利益日（+0.5% / +1%）— 上限リスク r を使った場合
    pd05 = sum(1 for _, _, net in rows if net * r >= 0.5)
    pd10 = sum(1 for _, _, net in rows if net * r >= 1.0)

    # 一貫性：最大の単日利益 / 総利益（r に依存しない）
    best = max(net for _, _, net in rows)
    consist = best / total_r * 100 if total_r > 0 else float("nan")

    print(f"\n=== {name} ===")
    print(f"  期間 {rows[0][0]}〜{rows[-1][0]} / {n_days}日 / {n_trades}トレード / 勝率 {wr:.1f}%")
    print(f"  総損益 {total_r:+.0f}R / 最大DD {dd:.0f}R / 1日最大トレード数 {max_n}")
    print(f"  リスク上限: DD制限から {r_dd:.3f}% / 銘柄リスク制限から {r_cap:.3f}% → 採用 {r:.3f}%")
    print(f"  → 全期間リターン {total_r * r:+.1f}%（利益目標 {TARGET}%）")
    print(f"  → 利益日(+0.5%) {pd05}日 / (+1.0%) {pd10}日（必要 3日）")
    print(f"  → 一貫性 最大単日 {consist:.1f}%（上限 {CONSIST}%）")
    return dict(name=name, r=r, r_dd=r_dd, r_cap=r_cap, total_r=total_r, dd=dd,
                max_n=max_n, pd05=pd05, pd10=pd10, consist=consist, days=n_days,
                ret=total_r * r)


results = [report(p, series(d["daily"][p])) for p in pairs]

# 全ペア合算（同日を合算。銘柄ごとにCAP、合計はDaily Loss Limitまで）
merged = {}
per_pair_n = {}
for p in pairs:
    for k, v in d["daily"][p].items():
        a = merged.setdefault(k, [0, 0])
        a[0] += v["w"] + v["l"]
        a[1] += v["w"] - v["l"]
        per_pair_n.setdefault(k, []).append(v["w"] + v["l"])
rows_all = [(k, v[0], v[1]) for k, v in sorted(merged.items())]
res_all = report("全ペア合算", rows_all)
# 合算時は「合計リスク ≤ Daily Loss Limit」も効く
r_total = DL / max(n for _, n, _ in rows_all)
r_sym = CAP / max(max(v) for v in per_pair_n.values())
print(f"  ※合算時の追加制約: 合計リスクから {r_total:.3f}% / 最大銘柄から {r_sym:.3f}%")

# 日次勝率の分布（利益日を作れるかの本質）
print("\n=== 利益日を作るのに必要な日次勝率（RR1:1・上の仮定下） ===")
print(f"  単一銘柄で +0.5%: 純益/トレード数 ≥ {0.5/CAP:.3f} → 日次勝率 ≥ {(1+0.5/CAP)/2*100:.1f}%")
print(f"  単一銘柄で +1.0%: 純益/トレード数 ≥ {1.0/CAP:.3f} → 日次勝率 ≥ {(1+1.0/CAP)/2*100:.1f}%")
print(f"  全銘柄合計で +0.5%: 純益/トレード数 ≥ {0.5/DL:.3f} → 日次勝率 ≥ {(1+0.5/DL)/2*100:.1f}%")
for p in pairs:
    rows = series(d["daily"][p])
    ok05 = sum(1 for _, n, net in rows if n and net / n >= 0.5 / CAP)
    ok10 = sum(1 for _, n, net in rows if n and net / n >= 1.0 / CAP)
    print(f"  {p:6s} 条件を満たす日: +0.5%用 {ok05:3d}日 / +1.0%用 {ok10:3d}日 （全{len(rows)}日）")
ok05 = sum(1 for _, n, net in rows_all if n and net / n >= 0.5 / DL)
print(f"  合算   条件を満たす日: +0.5%用 {ok05:3d}日 （全{len(rows_all)}日）")
