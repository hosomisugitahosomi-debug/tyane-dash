#!/usr/bin/env python3
"""バイナリーオプションのロジック検証。

データ: tick_data_final の 1秒OHLC(bid, UTC) parquet
判定  : エントリー時刻 t の close と t+満期秒 の close を比較。
        HIGH は close(t+K) > close(t) で勝ち。同値は引き分け(集計から除外)。

シグナルは t 時点までの価格しか見ない（未来を覗かない）。
"""
import argparse, glob, json, os, sys
import numpy as np
import pandas as pd

BREAKEVEN = 52.6  # ペイアウト1.90の損益分岐勝率(%)


def load_day(path):
    """1秒グリッドに揃えた close 系列を返す（欠損秒は直前値で補完）。"""
    df = pd.read_parquet(path)
    full = pd.date_range(df.index.min(), df.index.max(), freq="1s")
    return df["close"].reindex(full).ffill()


# ---------- シグナル ----------
# 返り値: +1=HIGH(上がる方に賭ける) / -1=LOW / 0=見送り
# p は「エントリー時刻ごとの価格」(1分間隔)。i 番目より後ろは絶対に見ない。

def sig_momentum(p, lookback=1):
    d = p.diff(lookback)
    return np.sign(d).fillna(0)


def sig_reversal(p, lookback=1):
    return -sig_momentum(p, lookback)


def sig_bollinger(p, n=20, k=2.0):
    """終値がバンド外なら逆張り。"""
    ma = p.rolling(n).mean()
    sd = p.rolling(n).std()
    s = pd.Series(0.0, index=p.index)
    s[p > ma + k * sd] = -1      # 上抜け → LOW
    s[p < ma - k * sd] = 1       # 下抜け → HIGH
    return s


def sig_rsi(p, n=14, hi=70, lo=30):
    d = p.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    s = pd.Series(0.0, index=p.index)
    s[rsi > hi] = -1
    s[rsi < lo] = 1
    return s


def sig_ma_dev(p, n=20, mult=1.5):
    """MA からの乖離が平常の mult 倍を超えたら逆張り。"""
    ma = p.rolling(n).mean()
    dev = p - ma
    scale = dev.abs().rolling(100).mean()
    s = pd.Series(0.0, index=p.index)
    s[dev > mult * scale] = -1
    s[dev < -mult * scale] = 1
    return s


def sig_always_high(p):
    return pd.Series(1.0, index=p.index)


RULES = {
    "常にHIGH(基準線)":      sig_always_high,
    "順張り 1分":            lambda p: sig_momentum(p, 1),
    "順張り 3分":            lambda p: sig_momentum(p, 3),
    "順張り 5分":            lambda p: sig_momentum(p, 5),
    "逆張り 1分":            lambda p: sig_reversal(p, 1),
    "逆張り 3分":            lambda p: sig_reversal(p, 3),
    "逆張り 5分":            lambda p: sig_reversal(p, 5),
    "ボリンジャー20/2σ逆張り": lambda p: sig_bollinger(p, 20, 2.0),
    "ボリンジャー20/2.5σ逆張り": lambda p: sig_bollinger(p, 20, 2.5),
    "RSI14 70/30逆張り":     lambda p: sig_rsi(p, 14, 70, 30),
    "RSI14 80/20逆張り":     lambda p: sig_rsi(p, 14, 80, 20),
    "MA20乖離1.5倍逆張り":    lambda p: sig_ma_dev(p, 20, 1.5),
}


def backtest_day(close_1s, expiry_sec, entry_step_min):
    """エントリー時刻の価格系列と、満期時の価格を返す。"""
    starts = close_1s.index[::60][::entry_step_min]          # 分足の境目
    ends = starts + pd.Timedelta(seconds=expiry_sec)
    ok = ends <= close_1s.index[-1]
    starts, ends = starts[ok], ends[ok]
    p_in = close_1s.reindex(starts)
    p_out = close_1s.reindex(ends)
    return pd.Series(p_in.values, index=starts), pd.Series(p_out.values, index=starts)


def run(files, expiry_sec, entry_step_min):
    rows = []
    for f in sorted(files):
        name = os.path.basename(f)
        sym, day = name.split("_")[0], name.split("_")[1]
        c = load_day(f)
        p_in, p_out = backtest_day(c, expiry_sec, entry_step_min)
        move = np.sign(p_out - p_in)                          # +1 上昇 / -1 下落 / 0 同値
        for rule, fn in RULES.items():
            s = fn(p_in)
            traded = s != 0
            m = move[traded]
            sg = s[traded]
            tie = (m == 0)
            win = (sg == m) & ~tie
            loss = (sg == -m) & ~tie
            rows.append(dict(symbol=sym, day=day, rule=rule, hour=-1,
                             n=int((~tie).sum()), w=int(win.sum()), l=int(loss.sum()),
                             ties=int(tie.sum()),
                             n_high=int(((sg == 1) & ~tie).sum()),
                             n_low=int(((sg == -1) & ~tie).sum()),
                             mkt_up=int((m == 1).sum())))
            # 時間帯別(UTC)
            hrs = pd.Series(p_in.index.hour, index=p_in.index)[traded]
            for h, idx in hrs.groupby(hrs).groups.items():
                mh, sh = m.loc[idx], sg.loc[idx]
                th = (mh == 0)
                rows.append(dict(symbol=sym, day=day, rule=rule, hour=int(h),
                                 n=int((~th).sum()), w=int(((sh == mh) & ~th).sum()),
                                 l=int(((sh == -mh) & ~th).sum()), ties=int(th.sum()),
                                 n_high=int(((sh == 1) & ~th).sum()),
                                 n_low=int(((sh == -1) & ~th).sum()),
                                 mkt_up=int((mh == 1).sum())))
    return pd.DataFrame(rows)


def summarize(df):
    """ドリフト補正つきの集計。

    帰無仮説 = 「シグナルに予測力はゼロ。ただし相場のドリフトはそのまま」
    その場合の期待勝率 = (HIGHを出した回数 x 上昇率 + LOWを出した回数 x 下落率) / 全体。
    実測勝率がこれを有意に上回って初めて「ロジックに意味がある」と言える。
    """
    g = df[df.hour == -1].groupby("rule")[
        ["n", "w", "l", "ties", "n_high", "n_low", "mkt_up"]].sum()
    g["wr"] = g.w / g.n * 100
    p_up = g.mkt_up / g.n                                    # そのルールが張った局面の上昇率
    g["期待勝率"] = (g.n_high * p_up + g.n_low * (1 - p_up)) / g.n * 100
    g["優位性"] = g.wr - g["期待勝率"]                        # ドリフトを除いた純粋な予測力
    g["±2σ"] = 2 * np.sqrt(0.25 / g.n) * 100
    g["判定"] = np.where(g["優位性"] - g["±2σ"] > 0, "◎予測力あり",
                 np.where(g["優位性"] + g["±2σ"] < 0, "×逆効果", "―誤差内"))
    g["分岐超"] = np.where(g.wr - g["±2σ"] > BREAKEVEN, "○", "―")
    return g.sort_values("優位性", ascending=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/*.parquet")
    ap.add_argument("--expiry", type=int, default=180, help="満期(秒)")
    ap.add_argument("--step", type=int, default=1, help="エントリー間隔(分)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    files = glob.glob(a.data)
    if not files:
        sys.exit(f"データが見つかりません: {a.data}")
    df = run(files, a.expiry, a.step)
    s = summarize(df)
    print(f"\n=== 満期{a.expiry}秒 / エントリー{a.step}分毎 / {len(files)}ファイル / 分岐{BREAKEVEN}% ===")
    print(s[["n", "wr", "期待勝率", "優位性", "±2σ", "判定", "分岐超"]].round(2).to_string())
    if a.out:
        df.to_csv(a.out, index=False)
