"""1秒OHLC(bid のみ)のparquetを、ティック検証と同じ形に変換する。

tick_data_final の1秒足には ask が無いのでスプレッドは実測できない。
bid=ask=close として渡し、スプレッドは後から仮定値で差し引く。
"""
import pandas as pd


def load_1sec_as_tick(path):
    df = pd.read_parquet(path)
    c = df["close"]
    return pd.DataFrame({"bid": c, "ask": c}, index=df.index)
