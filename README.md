# 📈 Benjamin Graham Conservative Stock Screener

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Graham Approved](https://img.shields.io/badge/Graham-Approved-green.svg)](https://en.wikipedia.org/wiki/Benjamin_Graham)

A Python tool that scans the NYSE universe for undervalued stocks using Benjamin Graham's conservative investment principles. Find true value investments with mathematical precision and safety-first approach.

![Graham Screener Demo](https://via.placeholder.com/800x400/1f2937/white?text=Benjamin+Graham+Stock+Screener)

## Features

- **Conservative Analysis**: Applies Graham's strict criteria with safety-first approach
- **Multiple Valuation Methods**: Earnings Power Value (EPV), Asset-based, and Conservative DCF
- **Full Audit Trails**: Links to SEC filings and detailed assumptions
- **Comprehensive Reports**: CSV summaries and detailed markdown reports per company
- **Pluggable Data Sources**: Support for Alpha Vantage, Financial Modeling Prep, and more

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/yourusername/benjamin-graham-screener.git
cd benjamin-graham-screener
pip install -r requirements.txt
```

### 2. Set Up API Keys
```bash
cp src/api_keys_template.py src/api_keys.py
# Edit src/api_keys.py with your Alpha Vantage API keys
```

### 3. Run Your First Screen
```bash
# Test with dry run (no API calls)
python graham_scan.py --dry_run --random_sample 5

# Screen 25 random NYSE stocks  
python graham_scan.py --random_sample 25 --top 10

# Screen custom stock list
python graham_scan.py --tickers_csv my_stocks.csv --top 5
```

📖 **[Full Setup Instructions](SETUP.md)** | 🤝 **[Contributing Guide](CONTRIBUTING.md)**

## Graham Screening Criteria

The screener applies Benjamin Graham's conservative investment criteria:

1. **Current Ratio ≥ 2.0** - Strong liquidity position
2. **Debt/Equity ≤ 0.5** - Conservative leverage
3. **P/E Ratio ≤ 15.0** - Not overpaying for earnings
4. **P/B Ratio ≤ 1.5** - Not overpaying for assets  
5. **P/E × P/B ≤ 22.5** - Graham's combined metric
6. **Consistent Positive Earnings** - At least 5 years
7. **Margin of Safety ≥ 50%** - Substantial safety buffer
8. **Positive Book Value** - Real asset backing

## Valuation Methods

### 1. Earnings Power Value (EPV)
- No-growth valuation using normalized owner earnings
- 10% discount rate (conservative)
- Adjusted for maintenance capex

### 2. Asset-Based Valuation
- Prefers Net Current Asset Value (NCAV) when positive
- Falls back to Tangible Book Value with 20% haircut
- Excludes goodwill and intangibles

### 3. Conservative DCF
- Growth rates capped at 5% annually
- Terminal growth limited to 2%
- Elevated discount rates (12%)

## Output Files

- **`output/top_10.csv`** - Summary table of top stocks
- **`output/top_10.json`** - Machine-readable results with full data
- **`reports/<TICKER>.md`** - Detailed analysis per company

## Command Line Options

```bash
python graham_scan.py [OPTIONS]

Options:
  --universe {nyse,nasdaq,all}     Stock universe to scan [default: nyse]
  --tickers_csv PATH              Custom ticker CSV file
  --top INTEGER                   Number of top stocks [default: 10]
  --years INTEGER                 Years of data to analyze [default: 7]
  --min_market_cap FLOAT          Minimum market cap filter
  --data_provider {alpha_vantage,fmp,tiingo,polygon}
                                 Financial data provider [default: alpha_vantage]
  --api_key TEXT                  API key for data provider
  --output_dir PATH               Output directory [default: output]
  --verbose                       Enable verbose logging
  --dry_run                       Test mode without API calls
```

## Data Providers

### Alpha Vantage (Default)
- Free tier available
- Set API_KEY environment variable or use --api_key

### Financial Modeling Prep
- Professional financial data
- Requires paid subscription

### Tiingo & Polygon
- Coming soon

## Configuration

The screener uses conservative defaults but can be customized:

```python
# In src/config.py
min_current_ratio = 2.0
max_debt_to_equity = 0.5
min_margin_of_safety = 0.5  # 50%
capex_multiplier = 1.2      # 20% capex haircut
```

## Example Report Structure

Each company gets a detailed markdown report:

```
# Apple Inc (AAPL)
## Executive Summary
- Current Price: $150.00
- Intrinsic Value: $180.00  
- Margin of Safety: 16.7%
- Graham Score: 85/100

## Key Financial Metrics
| Metric | Value | Criterion | Status |
|--------|-------|-----------|--------|
| Current Ratio | 2.8 | ≥ 2.0 | ✅ Pass |

## Valuation Analysis
### 1. Earnings Power Value (EPV)
- Intrinsic Value: $165.00
- Conservative assumptions...

## Risk Factors & Audit Trail
- Links to SEC filings
- Detailed assumptions
- Data sources
```

## Testing

```bash
pytest tests/
```

## Conservative Principles

This tool embodies Benjamin Graham's investment philosophy:

- **Safety First**: Multiple safety checks and conservative assumptions
- **Margin of Safety**: Substantial buffer against errors
- **Tangible Assets**: Focus on real, measurable value
- **Consistent Earnings**: Proven business models
- **Low Leverage**: Financial strength over growth
- **Reasonable Prices**: Never overpay, even for quality

## Limitations

- Quantitative screening only - qualitative analysis still required
- Historical data may not predict future performance  
- Market conditions can affect value investing returns
- Some excellent companies may be filtered out by strict criteria

## License

MIT License - See LICENSE file for details.

## 🎯 Project Status

- ✅ **Fully Functional**: Complete implementation of Graham's methodology
- ✅ **API Integration**: Alpha Vantage support with rate limiting
- ✅ **Random Sampling**: Efficiently test with limited API calls  
- ✅ **Comprehensive Testing**: Unit tests and validation
- 🔄 **Active Development**: Accepting contributions and feature requests

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

Areas where help is needed:
- Additional data providers (Tiingo, Polygon, etc.)
- Sector-specific analysis improvements
- Performance optimizations
- Documentation and examples

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Not investment advice. Always consult financial professionals and conduct your own research before making investment decisions.

## 🏆 Acknowledgments

- **Benjamin Graham** - The father of value investing
- **Alpha Vantage** - Financial data API
- **Python Community** - Amazing libraries and tools

---

⭐ **Star this repository if you find it useful!**