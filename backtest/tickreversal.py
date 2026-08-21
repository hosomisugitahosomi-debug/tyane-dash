#!/usr/bin/env python3
"""TickReversal_v2.mq4 (v3.10) のロジックをFX用に移植したバックテスト。

EAから抜き出した仕様（UIとシャドーログは除外、本命ロジックのみ）:

  単位   : JPYペアは 1pip = 0.01
  閾値X  : 銘柄 x JST時間帯 で決まる (gCSym/gCH1/gCH2/gCX)
  (1)    : 1秒の値動き |d| >= X で逆方向にエントリー。発火後 180秒は同一銘柄ロック
  (2)    : (1)が |d| >= X+1.0 で出た場合のみ武装。120秒以内に
           「1.0pips 逆行(戻り)」してから「発火価格 ±0.3pips に再到達」で再エントリー
  (3)    : M1確定足で 実体 >= 直近30本平均の5.0倍 かつ |(終値-MA20)/StdDev20| >= 2.5
           ただしその足の最大1秒変動が X+1.0 以上なら (1)と重複するので除外
  (4)    : (3)の後、(2)と同じ戻り→再到達ロジック。基準価格はM1終値
  無音   : 300秒以上レートが止まったら基準を入れ替えるだけで発火させない
  M1飛び : M1が1800秒以上飛んだら (3)を51本休む

FX化:
  sg=+1 -> 売り(Low) / sg=-1 -> 買い(High)
  売り: bid で入り ask で出る / 買い: ask で入り bid で出る  (スプレッドは実測ティック)
  決済: (A) 180秒経過で成行  (B) SL/TP を X pips に置く(最大保有180秒)
"""
import numpy as np
import pandas as pd

UNIT = 0.01                # JPYペアの1pip
LOCK_SEC = 180
RE_BACK = 1.0              # InpReBackPip
RE_BAND = 0.3              # InpReBandPip
RE_WAIT = 120              # InpReMaxWaitSec
JUDGE_SEC = 180            # InpJudgeSec
STALE_SEC = 300            # InpStaleSec
GAP_SEC = 1800             # InpGapSec
NB1, MAPER, R1, S1 = 30, 20, 5.0, 2.5

# gCSym / gCH1 / gCH2 / gCX ... 時間はJST
CELLS = {
    "USDJPY": [(8, 15, 5.0, "東京"), (2, 4, 2.0, "NY後半")],
    "EURJPY": [(16, 21, 4.0, "欧州"), (22, 1, 3.0, "NY前半"), (2, 4, 2.0, "NY後半")],
    "GBPJPY": [(8, 15, 4.0, "東京"), (2, 4, 2.0, "NY後半")],
    "AUDJPY": [(16, 21, 3.0, "欧州"), (22, 1, 4.0, "NY前半"), (2, 4, 2.0, "NY後半")],
}


def active_x(sym, jst_hour):
    """ActiveX() の移植。最初に一致したセルの閾値を返す。範囲外は0(=停止)。"""
    for h1, h2, x, _ in CELLS[sym]:
        inside = (h1 <= jst_hour <= h2) if h1 <= h2 else (jst_hour >= h1 or jst_hour <= h2)
        if inside:
            return x
    return 0.0


def x_by_second(sym, idx):
    """秒グリッドの各時刻に対する閾値X。idxはUTC。"""
    jst_h = (idx.hour + 9) % 24
    out = np.zeros(len(idx))
    for h1, h2, x, _ in CELLS[sym]:
        m = (jst_h >= h1) & (jst_h <= h2) if h1 <= h2 else (jst_h >= h1) | (jst_h <= h2)
        out = np.where((out == 0) & m, x, out)
    return out


def to_second_grid(tick):
    """ティックを1秒グリッドに。各秒の「最後のbid/ask」を取り、欠損秒は直前値。

    stale: 直前ティックから STALE_SEC 以上空いた区間は発火禁止フラグを立てる。
    """
    t = tick.copy()
    t.index = t.index.floor("s")
    last = t.groupby(level=0).last()
    grid = pd.date_range(last.index.min(), last.index.max(), freq="1s")
    b = last["bid"].reindex(grid).ffill()
    a = last["ask"].reindex(grid).ffill()
    # 「実際にティックがあった秒」からの経過秒 → 無音の長さ
    had = pd.Series(False, index=grid)
    had.loc[last.index] = True
    since = np.zeros(len(grid), dtype=np.int64)
    n = 0
    hv = had.values
    for i in range(len(grid)):
        n = 0 if hv[i] else n + 1
        since[i] = n
    stale = since > STALE_SEC
    return b.values, a.values, grid, stale


def m1_signals(b, grid, d, x_arr):
    """(3) の発火秒を返す: [(second_index, sg, m1_close_price), ...]"""
    minute = (np.arange(len(grid)) // 60)
    df = pd.DataFrame({"m": minute, "b": b})
    o = df.groupby("m")["b"].first().values
    c = df.groupby("m")["b"].last().values
    # その足の中での最大1秒上昇 / 最大1秒下落
    dd = pd.DataFrame({"m": minute, "d": d})
    mx_up = dd.groupby("m")["d"].max().values
    mx_dn = -dd.groupby("m")["d"].min().values
    n = len(c)
    body = np.abs(o - c) / UNIT
    avg = pd.Series(body).rolling(NB1).mean().shift(1).values     # bars 2..31
    ma = pd.Series(c).rolling(MAPER).mean().values
    sd = pd.Series(c).rolling(MAPER).std(ddof=0).values
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = body / avg
        sig = (c - ma) / sd
    fires = []
    warm = 0
    for k in range(1, n):
        # M1が飛んだ判定(1秒グリッドは連続なので、無音秒で代用)
        if warm > 0:
            warm -= 1
            continue
        if np.isnan(ratio[k]) or np.isnan(sig[k]) or sd[k] <= 0:
            continue
        if ratio[k] < R1 or abs(sig[k]) < S1:
            continue
        sg = 1.0 if sig[k] > 0 else -1.0
        sec = (k + 1) * 60                       # 次の足の頭で確定検知
        if sec >= len(grid):
            continue
        x = x_arr[sec]
        if x <= 0:
            continue
        big = mx_up[k] if sig[k] > 0 else mx_dn[k]
        if big >= x + 1.0:                       # (1)と重複するので除外
            continue
        fires.append((sec, sg, c[k]))
    return fires


def watch_reentry(b, start, p0, sg, limit):
    """(2)(4) 共通: 戻り -> 再到達 を探す。見つかった秒を返す。無ければ None。"""
    end = min(start + RE_WAIT, len(b) - 1)
    back = False
    for s in range(start + 1, end + 1):
        dv = (b[s] - p0) / UNIT * sg
        if not back:
            if -dv >= RE_BACK:
                back = True
        elif abs(dv) <= RE_BAND:
            return s
    return None


def signals_for_day(tick, sym):
    """1日分のティックから (1)(2)(3)(4) の発火を全部出す。"""
    b, a, grid, stale = to_second_grid(tick)
    x_arr = x_by_second(sym, grid)
    d = np.zeros(len(b))
    d[1:] = (b[1:] - b[:-1]) / UNIT
    d[stale] = 0.0                                # 無音明けは発火させない

    out = []
    # --- (1) と (2)
    cand = np.where((x_arr > 0) & (np.abs(d) >= x_arr) & (~stale))[0]
    lock_end = -1
    for s in cand:
        if s < lock_end:
            continue
        x = x_arr[s]
        sg = 1.0 if d[s] > 0 else -1.0
        lock_end = s + LOCK_SEC
        out.append(dict(sec=s, typ=1, sg=sg, x=x))
        if abs(d[s]) >= x + 1.0:
            r = watch_reentry(b, s, b[s], sg, RE_WAIT)
            if r is not None:
                out.append(dict(sec=r, typ=2, sg=sg, x=x))
    # --- (3) と (4)
    for sec, sg, c1 in m1_signals(b, grid, d, x_arr):
        out.append(dict(sec=sec, typ=3, sg=sg, x=x_arr[sec]))
        r = watch_reentry(b, sec, c1, sg, RE_WAIT)
        if r is not None:
            out.append(dict(sec=r, typ=4, sg=sg, x=x_arr[sec]))

    for o in out:
        o["time"] = grid[o["sec"]]
    return out, b, a, grid


def simulate(sig, b, a, grid, mode):
    """1発火をFXトレードとして決済する。

    mode="time": JUDGE_SEC 経過で成行
    mode="sltp": SL/TP を X pips に置く(最大保有 JUDGE_SEC)
    戻り: pips単位の損益(スプレッド込み)。約定不能なら None
    """
    s, sg, x = sig["sec"], sig["sg"], sig["x"]
    end = s + JUDGE_SEC
    if end >= len(b):
        return None
    if sg > 0:                       # 売り: bidで入り askで出る
        entry = b[s]
        exits = a[s + 1:end + 1]
        pnl_path = (entry - exits) / UNIT
    else:                            # 買い: askで入り bidで出る
        entry = a[s]
        exits = b[s + 1:end + 1]
        pnl_path = (exits - entry) / UNIT
    if mode == "time":
        return float(pnl_path[-1])
    hit_tp = np.where(pnl_path >= x)[0]
    hit_sl = np.where(pnl_path <= -x)[0]
    i_tp = hit_tp[0] if len(hit_tp) else 10 ** 9
    i_sl = hit_sl[0] if len(hit_sl) else 10 ** 9
    if i_tp == i_sl == 10 ** 9:
        return float(pnl_path[-1])
    return float(x) if i_tp < i_sl else float(-x)


def simulate_limit(sig, b, a, offset_pips, fill_window, tp_pips=None, sl_pips=None,
                   max_hold=JUDGE_SEC):
    """成行ではなく指値でエントリーした場合。

    売り(sg=+1): スパイクの上に売り指値を置く → bid が指値まで戻ったら約定
    買い(sg=-1): スパイクの下に買い指値を置く → ask が指値まで下がったら約定
    offset_pips 分だけ有利な価格で入れるが、そこまで伸びなければ約定しない。

    戻り: (pips, 約定したか)。約定しなければ (None, False)
    """
    s, sg, x = sig["sec"], sig["sg"], sig["x"]
    if tp_pips is None:
        tp_pips = x
    if sl_pips is None:
        sl_pips = x
    end_scan = min(s + 1 + fill_window, len(b))
    if sg > 0:                                   # 売り
        target = b[s] + offset_pips * UNIT
        hit = np.where(b[s + 1:end_scan] >= target)[0]
    else:                                        # 買い
        target = a[s] - offset_pips * UNIT
        hit = np.where(a[s + 1:end_scan] <= target)[0]
    if len(hit) == 0:
        return None, False
    f = s + 1 + int(hit[0])                      # 約定した秒
    end = f + max_hold
    if end >= len(b):
        return None, False
    if sg > 0:                                   # 売り: 決済は ask を買う
        path = (target - a[f + 1:end + 1]) / UNIT
    else:                                        # 買い: 決済は bid を売る
        path = (b[f + 1:end + 1] - target) / UNIT
    i_tp = np.where(path >= tp_pips)[0]
    i_sl = np.where(path <= -sl_pips)[0]
    t_tp = i_tp[0] if len(i_tp) else 10 ** 9
    t_sl = i_sl[0] if len(i_sl) else 10 ** 9
    if t_tp == t_sl == 10 ** 9:
        return float(path[-1]), True
    return (float(tp_pips) if t_tp < t_sl else float(-sl_pips)), True
