# **FOI Analysis: De-dollarisation**

---

## Data Sources

### Pulled with code

**U.S. Treasury holdings by country (TIC), via FRED**: `scripts/01_download.py`
- China: [FORTREASPOS41408](https://fred.stlouisfed.org/series/FORTREASPOS41408), [FORLTTREASPOS41408](https://fred.stlouisfed.org/series/FORLTTREASPOS41408), [FORLTTREASNET41408](https://fred.stlouisfed.org/series/FORLTTREASNET41408), [FORLTTREASVALCHG41408](https://fred.stlouisfed.org/series/FORLTTREASVALCHG41408)
- Brazil: [FORTREASPOS30309](https://fred.stlouisfed.org/series/FORTREASPOS30309), [FORLTTREASPOS30309](https://fred.stlouisfed.org/series/FORLTTREASPOS30309), [FORLTTREASNET30309](https://fred.stlouisfed.org/series/FORLTTREASNET30309), [FORLTTREASVALCHG30309](https://fred.stlouisfed.org/series/FORLTTREASVALCHG30309)
- India: [FORTREASPOS42102](https://fred.stlouisfed.org/series/FORTREASPOS42102), [FORLTTREASPOS42102](https://fred.stlouisfed.org/series/FORLTTREASPOS42102), [FORLTTREASNET42102](https://fred.stlouisfed.org/series/FORLTTREASNET42102), [FORLTTREASVALCHG42102](https://fred.stlouisfed.org/series/FORLTTREASVALCHG42102)
- Russia: [FORTREASPOS16101](https://fred.stlouisfed.org/series/FORTREASPOS16101), [FORLTTREASPOS16101](https://fred.stlouisfed.org/series/FORLTTREASPOS16101), [FORLTTREASNET16101](https://fred.stlouisfed.org/series/FORLTTREASNET16101), [FORLTTREASVALCHG16101](https://fred.stlouisfed.org/series/FORLTTREASVALCHG16101)
- Grand Total: [FORTREASPOS99996](https://fred.stlouisfed.org/series/FORTREASPOS99996), [FORLTTREASPOS99996](https://fred.stlouisfed.org/series/FORLTTREASPOS99996), [FORLTTREASNET99996](https://fred.stlouisfed.org/series/FORLTTREASNET99996), [FORLTTREASVALCHG99996](https://fred.stlouisfed.org/series/FORLTTREASVALCHG99996)
- Foreign Official: [FORTREASPOS99990](https://fred.stlouisfed.org/series/FORTREASPOS99990), [FORLTTREASPOS99990](https://fred.stlouisfed.org/series/FORLTTREASPOS99990), [FORLTTREASNET99990](https://fred.stlouisfed.org/series/FORLTTREASNET99990), [FORLTTREASVALCHG99990](https://fred.stlouisfed.org/series/FORLTTREASVALCHG99990)
- Cross-check: [Treasury Major Foreign Holders historical table](https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/mfhhis01.html)

**Interest rates (FRED)**: `scripts/01_download.py`
- [GS10](https://fred.stlouisfed.org/series/GS10), [DGS10](https://fred.stlouisfed.org/series/DGS10), [FEDFUNDS](https://fred.stlouisfed.org/series/FEDFUNDS), [T10YIE](https://fred.stlouisfed.org/series/T10YIE), [THREEFYTP10](https://fred.stlouisfed.org/series/THREEFYTP10), [TB3MS](https://fred.stlouisfed.org/series/TB3MS)

**Market prices (Yahoo Finance via yfinance)**: `scripts/01_download.py`
- [SPY](https://finance.yahoo.com/quote/SPY/), [AGG](https://finance.yahoo.com/quote/AGG/), [IEF](https://finance.yahoo.com/quote/IEF/), [GLD](https://finance.yahoo.com/quote/GLD/)

### Downloaded manually, then extracted with code

**Gold reserves (World Gold Council)**: `scripts/03_extract_wgc_gold.py`
- [Gold reserves by country](https://www.gold.org/goldhub/data/gold-reserves-by-country) (quarterly export, Q4 2018 – Q4 2025)

**Global FX reserve composition (IMF COFER)**: `scripts/04_extract_cofer.py`
- [IMF COFER dataset](https://data.imf.org/en/datasets/IMF.STA:COFER) (release of 30 Sep 2026)

### Entered by hand

**Russia, reserve currency shares (Bank of Russia)**
- [Annual Report 2018](https://cbr.ru/Collection/Collection/File/24037/ar_2018_e.pdf)
- [Annual Report 2019](https://cbr.ru/Collection/Collection/File/29420/ar_2019.pdf)
- [Annual Report 2021](https://cbr.ru/collection/collection/file/40915/ar_2021.pdf)

**India, gold holdings (Reserve Bank of India)**
- [Half Yearly Report, Oct 2018 – Mar 2019](https://www.rbi.org.in/Scripts/PublicationsView.aspx?id=18952)
- [Half Yearly Report, Apr – Sep 2025](https://www.rbi.org.in/Scripts/PublicationsView.aspx?id=23437)

**China, FX reserves (SAFE)**
- [End-December 2018](https://www.safe.gov.cn/en/2020/0604/1697.html)
- [End-December 2025](https://www.safe.gov.cn/en/2026/0107/2382.html)