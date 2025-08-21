#!/usr/bin/env python3
"""
Example usage of the Graham screener with mock data
"""

import asyncio
import logging
from pathlib import Path

from src.config import Config
from src.screener import GrahamScreener
from src.data_providers import DataProviderFactory


async def run_example():
    """Run example screening with dry run mode"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create config with dry run mode
    config = Config(
        universe='nyse',
        top_count=5,
        years=7,
        data_provider='alpha_vantage',
        output_dir=Path('example_output'),
        dry_run=True,  # Don't make real API calls
        verbose=True
    )
    
    logger.info("Starting Graham screener example (dry run mode)")
    
    try:
        # Create data provider
        data_provider = DataProviderFactory.create(config)
        
        # Create screener
        screener = GrahamScreener(config, data_provider)
        
        # Run the screen
        results = await screener.run_screen()
        
        if results:
            logger.info(f"Example completed! Found {len(results)} stocks")
            logger.info("Check example_output/ directory for results")
            
            # Print top result
            top_stock = results[0]
            logger.info(f"Top stock: {top_stock.ticker} - {top_stock.company_name}")
            logger.info(f"Graham Score: {top_stock.graham_score:.1f}")
            logger.info(f"Margin of Safety: {top_stock.margin_of_safety:.1%}")
        else:
            logger.info("No stocks found meeting criteria")
            
    except Exception as e:
        logger.error(f"Example failed: {str(e)}")
        raise
    
    finally:
        # Cleanup
        if hasattr(data_provider, 'close'):
            await data_provider.close()


if __name__ == "__main__":
    asyncio.run(run_example())