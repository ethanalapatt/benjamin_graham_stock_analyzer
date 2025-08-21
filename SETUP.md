# Setup Instructions

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/benjamin-graham-screener.git
cd benjamin-graham-screener
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up API Keys
```bash
# Copy the template file
cp src/api_keys_template.py src/api_keys.py

# Edit with your API keys
nano src/api_keys.py  # or use your preferred editor
```

Add your Alpha Vantage API keys to the `ALPHA_VANTAGE_KEYS` list:
```python
ALPHA_VANTAGE_KEYS = [
    "YOUR_ACTUAL_KEY_1",
    "YOUR_ACTUAL_KEY_2",
    # ... add more keys
]
```

### 4. Get Alpha Vantage API Keys
- Go to [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
- Sign up for free API keys
- Each key gives you 25 requests per day
- Add multiple keys for higher limits

### 5. Test Installation
```bash
# Test basic functionality
python test_basic.py

# Test with dry run (no API calls)
python graham_scan.py --dry_run --random_sample 5 --verbose

# Test with real API calls (uses your keys)
python graham_scan.py --random_sample 3 --top 3
```

## Usage Examples

```bash
# Randomly sample 25 stocks from NYSE
python graham_scan.py --random_sample 25 --top 10

# Screen custom stock list
python graham_scan.py --tickers_csv my_stocks.csv --top 5

# Large cap stocks only
python graham_scan.py --random_sample 50 --min_market_cap 1000000000

# Verbose output for debugging
python graham_scan.py --random_sample 10 --verbose
```

## Configuration

### Environment Variables (Optional)
```bash
export ALPHA_VANTAGE_API_KEY=your_key_here
export OUTPUT_DIR=my_analysis
```

### Custom Screening Criteria
Edit `src/config.py` to adjust Graham's criteria:
```python
min_current_ratio = 2.0          # Liquidity requirement
max_debt_to_equity = 0.5         # Debt limit
min_margin_of_safety = 0.5       # 50% safety margin
```

## Troubleshooting

### Common Issues

**Import Error**: Make sure you copied `api_keys_template.py` to `api_keys.py`
```bash
cp src/api_keys_template.py src/api_keys.py
```

**Rate Limiting**: Alpha Vantage free tier is limited. Solutions:
- Use `--dry_run` for testing
- Use smaller `--random_sample` sizes
- Add more API keys to `api_keys.py`
- Wait between runs for limits to reset

**SSL Errors**: The code includes SSL workarounds for development environments

**No Qualifying Stocks**: This is normal! Graham's criteria are very strict:
- Only 1-5% of stocks typically pass all filters
- This selectivity is exactly what Graham intended
- Try larger sample sizes or wait for market corrections

### Getting Help

1. Check the [README](README.md) for detailed documentation
2. Review [CONTRIBUTING](CONTRIBUTING.md) for development guidelines
3. Open an issue on GitHub for bugs or questions
4. Run `python graham_scan.py --help` for command options

## Advanced Configuration

### Adding More Data Providers
The system supports multiple data providers. To add new ones:
1. Implement the `DataProvider` interface
2. Add to `DataProviderFactory` 
3. Update configuration options

### Custom Output Formats
Reports are generated in multiple formats:
- `output/top_10.csv` - Spreadsheet summary
- `output/top_10.json` - Machine-readable data
- `output/reports/*.md` - Detailed company analysis

## Security Notes

- Never commit `api_keys.py` to version control
- The `.gitignore` file prevents accidental commits
- API keys are rotated automatically to manage rate limits
- Consider using environment variables in production