#!/usr/bin/env python3
"""TickReversalロジックをFXとして回し、プロップの合否条件で評価する。"""
import argparse, glob, os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tickreversal import signals_for_day, simulate, UNIT


def collect(files, sym, modes=("time", "sltp")):
    rows = []
    for f in sorted(files):
        day = os.path.basename(f).split("_")[1]
        t = pd.read_parquet(f)
        sigs, b, a, grid = signals_for_day(t, sym)
        spread = float(np.median((a - b) / UNIT))
        for s in sigs:
            r = dict(day=day, time=s["time"], typ=s["typ"], sg=int(s["sg"]),
                     x=s["x"], spread=spread)
            ok = True
            for m in modes:
                v = simulate(s, b, a, grid, m)
                if v is None:
                    ok = False
                    break
                r["pips_" + m] = v
            if ok:
                rows.append(r)
    return pd.DataFrame(rows)


def equity_run(df, col, risk_pct, target_pct, daily_limit_pct, dd_limit_pct):
    """1トレード = 閾値Xピップスを risk_pct とみなしてサイズを決める。

    戻り: 経過の要約。target到達 / daily違反 / DD違反 を判定する。
    """
    eq = 100.0
    peak = 100.0
    day_start = None
    cur_day = None
    max_dd = 0.0
    worst_day = 0.0
    curve = []
    hit_target_at = None
    breach = None
    for i, r in enumerate(df.itertuples()):
        if r.day != cur_day:
            cur_day = r.day
            day_start = eq
        eq += eq * (risk_pct / 100.0) * (getattr(r, col) / r.x)
        peak = max(peak, eq)
        dd = (peak - eq) / peak * 100
        max_dd = max(max_dd, dd)
        day_pl = (eq - day_start) / day_start * 100
        worst_day = min(worst_day, day_pl)
        curve.append(eq)
        if breach is None:
            if day_pl <= -daily_limit_pct:
                breach = f"日次損失 {day_pl:.2f}% ({r.day})"
            elif dd >= dd_limit_pct:
                breach = f"最大DD {dd:.2f}% ({r.day})"
        if hit_target_at is None and eq >= 100 + target_pct:
            hit_target_at = (i + 1, r.day)
    return dict(final=eq, ret=eq - 100, max_dd=max_dd, worst_day=worst_day,
                target=hit_target_at, breach=breach, curve=curve)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--sym", default="USDJPY")
    ap.add_argument("--target", type=float, default=2.0)
    ap.add_argument("--daily", type=float, default=5.0)
    ap.add_argument("--dd", type=float, default=10.0)
    ap.add_argument("--csv", default=None)
    a = ap.parse_args()

    files = sorted(glob.glob(a.data))
    df = collect(files, a.sym)
    if a.csv:
        df.to_csv(a.csv, index=False)
    if df.empty:
        sys.exit("シグナルが1件も出ませんでした")

    days = df.day.nunique()
    print(f"=== {a.sym} / {len(files)}営業日 / シグナル {len(df)}件 "
          f"(1日あたり {len(df)/days:.1f}件) ===")
    print(f"中央スプレッド {df.spread.median():.2f} pips\n")

    for col, lbl in [("pips_time", "180秒で成行決済"), ("pips_sltp", "SL/TP = X pips")]:
        print(f"--- {lbl} ---")
        g = df.groupby("typ")[col].agg(件数="count", 勝率=lambda s: (s > 0).mean() * 100,
                                       平均pips="mean", 合計pips="sum")
        g["勝率"] = g["勝率"].round(1)
        allrow = pd.DataFrame([dict(件数=len(df), 勝率=round((df[col] > 0).mean() * 100, 1),
                                    平均pips=df[col].mean(), 合計pips=df[col].sum())],
                              index=["合計"])
        print(pd.concat([g, allrow]).round(2).to_string())
        for risk in (0.25, 0.5, 1.0, 2.0):
            r = equity_run(df, col, risk, a.target, a.daily, a.dd)
            tg = f"{r['target'][0]}件目({r['target'][1]})" if r["target"] else "未到達"
            print(f"  リスク{risk:>4}%: 最終 {r['final']:7.2f}  "
                  f"最大DD {r['max_dd']:5.2f}%  最悪日 {r['worst_day']:6.2f}%  "
                  f"+{a.target}%到達 {tg:>18}  違反: {r['breach'] or 'なし'}")
        print()
