# Project Structure

```
benjamin-graham-screener/
├── README.md                    # Main documentation
├── SETUP.md                     # Setup instructions  
├── CONTRIBUTING.md              # Contribution guidelines
├── LICENSE                      # MIT license
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI/CD
│
├── graham_scan.py              # Main CLI application
├── test_basic.py               # Basic functionality test
├── simulate_findings.py        # Demo simulation
├── run_example.py              # Example usage
│
├── src/                        # Core library code
│   ├── __init__.py
│   ├── config.py               # Configuration management
│   ├── api_keys_template.py    # API key template (copy to api_keys.py)
│   ├── data_providers.py       # Data provider interfaces & implementations
│   ├── screener.py             # Main screening engine
│   ├── valuations.py           # Graham valuation methods
│   ├── reports.py              # Report generation
│   └── sec_filings.py          # SEC filing integration
│
├── tests/                      # Unit tests
│   ├── __init__.py
│   ├── test_valuations.py      # Valuation method tests
│   ├── test_screener.py        # Screener logic tests
│   └── test_data_providers.py  # Data provider tests
│
└── output/                     # Generated reports (git ignored)
    ├── top_10.csv              # Summary CSV
    ├── top_10.json             # Machine-readable results
    └── reports/                # Individual company reports
        ├── TICKER.md           # Detailed analysis per stock
        └── ...
```

## Key Components

### Core Engine (`src/`)
- **`screener.py`** - Main Graham screening logic
- **`valuations.py`** - EPV, DCF, and asset-based valuations  
- **`data_providers.py`** - Pluggable data source architecture
- **`config.py`** - Conservative screening parameters

### CLI Interface
- **`graham_scan.py`** - Command-line interface
- **`test_basic.py`** - Installation verification
- **`simulate_findings.py`** - Demo successful findings

### Data Integration
- **Alpha Vantage API** - Primary data source
- **SEC EDGAR** - Filing URLs for audit trails
- **NYSE Ticker Lists** - Universe generation
- **Rate Limiting** - Automatic key rotation

### Output Formats
- **CSV** - Spreadsheet-compatible summaries
- **JSON** - Machine-readable data
- **Markdown** - Detailed company reports
- **Console** - Real-time progress logging

### Testing & Quality
- **Unit Tests** - Comprehensive test coverage
- **CI/CD Pipeline** - Automated testing
- **Code Standards** - Linting and formatting
- **Documentation** - Extensive guides and examples

## Development Workflow

1. **Fork & Clone** - Get your own copy
2. **Install Dependencies** - `pip install -r requirements.txt`
3. **Set Up API Keys** - Copy template and add real keys
4. **Run Tests** - `pytest tests/`
5. **Test CLI** - `python graham_scan.py --dry_run`
6. **Make Changes** - Follow Graham's principles
7. **Submit PR** - Contribute back to community

## Security & Privacy

- **API Keys** - Never committed (in .gitignore)
- **Rate Limiting** - Respects API provider limits  
- **Error Handling** - Graceful failure modes
- **Data Validation** - Conservative assumptions

## Philosophy

Every component embodies Benjamin Graham's investment principles:
- **Safety First** - Conservative assumptions throughout
- **Margin of Safety** - Substantial buffers required
- **Tangible Value** - Focus on real, measurable assets
- **Proven Performance** - Consistent earnings history
- **Low Leverage** - Financial strength over growth