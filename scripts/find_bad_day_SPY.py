import yfinance as yf

d = yf.download(
    ["SPY", "IVV", "^GSPC"],
    start="2010-10-25",
    end="2010-12-03",
    auto_adjust=True,
    progress=False,
)["Close"]
print(d.round(2))
