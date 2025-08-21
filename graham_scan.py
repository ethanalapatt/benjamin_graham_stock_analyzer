#!/usr/bin/env python3
"""
Benjamin Graham Conservative Stock Screener
Scans NYSE universe for undervalued stocks using Graham's principles
"""

import argparse
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from src.screener import GrahamScreener
from src.data_providers import DataProviderFactory
from src.config import Config


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def main():
    parser = argparse.ArgumentParser(
        description="Benjamin Graham Conservative Stock Screener",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python graham_scan.py --universe nyse --top 10 --years 7
  python graham_scan.py --tickers_csv my_stocks.csv --top 5
  python graham_scan.py --universe nyse --min_market_cap 1000000000
  python graham_scan.py --random_sample 25 --top 10
  python graham_scan.py --random_sample 50 --dry_run --verbose
        """
    )
    
    parser.add_argument('--universe', choices=['nyse', 'nasdaq', 'all'],
                       default='nyse', help='Stock universe to scan')
    parser.add_argument('--tickers_csv', type=str,
                       help='CSV file with custom ticker list')
    parser.add_argument('--top', type=int, default=10,
                       help='Number of top stocks to return')
    parser.add_argument('--years', type=int, default=7,
                       help='Years of historical data to analyze')
    parser.add_argument('--min_market_cap', type=float,
                       help='Minimum market cap filter')
    parser.add_argument('--data_provider', 
                       choices=['alpha_vantage', 'fmp', 'tiingo', 'polygon'],
                       default='alpha_vantage',
                       help='Financial data provider')
    parser.add_argument('--api_key', type=str,
                       help='API key for data provider')
    parser.add_argument('--output_dir', type=str, default='output',
                       help='Output directory for reports')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--dry_run', action='store_true',
                       help='Run without making API calls (test mode)')
    parser.add_argument('--random_sample', type=int,
                       help='Randomly sample N stocks from the universe instead of screening all')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        config = Config(
            universe=args.universe,
            tickers_csv=args.tickers_csv,
            top_count=args.top,
            years=args.years,
            min_market_cap=args.min_market_cap,
            data_provider=args.data_provider,
            api_key=args.api_key,
            output_dir=Path(args.output_dir),
            dry_run=args.dry_run,
            random_sample=args.random_sample
        )
        
        logger.info(f"Starting Graham screener for {args.universe} universe")
        logger.info(f"Looking for top {args.top} stocks with {args.years} years of data")
        
        if args.random_sample:
            logger.info(f"Will randomly sample {args.random_sample} stocks from universe")
        
        data_provider = DataProviderFactory.create(config)
        screener = GrahamScreener(config, data_provider)
        
        results = await screener.run_screen()
        
        if results:
            logger.info(f"Screen completed successfully. Found {len(results)} qualifying stocks.")
            logger.info(f"Reports saved to {config.output_dir}")
        else:
            logger.warning("No stocks met the Graham criteria.")
            
    except Exception as e:
        logger.error(f"Screen failed: {str(e)}")
        return 1
        
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))