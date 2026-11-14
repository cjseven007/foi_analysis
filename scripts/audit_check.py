import pandas as pd

p = pd.read_csv("data/raw/market/etf_prices_monthly.csv", index_col=0)
for c in p:
    s = p[c].dropna()
    print(c, list(s[s.diff() == 0].index))
