"""Graham-style stock screener with safety-first approach"""

import asyncio
import logging
import random
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
import json

from .config import Config
from .data_providers import DataProvider, CompanyProfile, FinancialStatement
from .valuations import GrahamValuator, ValuationResult, FinancialMetrics
from .reports import ReportGenerator
from .sec_filings import SECFilingProvider


@dataclass
class ScreenResult:
    ticker: str
    company_name: str
    sector: str
    current_price: float
    intrinsic_value: float
    margin_of_safety: float
    triangulated_value: float
    valuations: List[ValuationResult]
    metrics: FinancialMetrics
    graham_score: float
    rank: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert ValuationResult objects to dicts
        result['valuations'] = [asdict(v) for v in self.valuations]
        result['metrics'] = asdict(self.metrics)
        return result


class GrahamScreener:
    """Benjamin Graham stock screener implementation"""
    
    def __init__(self, config: Config, data_provider: DataProvider):
        self.config = config
        self.data_provider = data_provider
        self.valuator = GrahamValuator(config)
        self.report_generator = ReportGenerator(config)
        self.sec_provider = SECFilingProvider(config)
        self.logger = logging.getLogger(__name__)
    
    async def run_screen(self) -> List[ScreenResult]:
        """Run the complete Graham screening process"""
        
        # Get universe of stocks to screen
        tickers = await self._get_screening_universe()
        if not tickers:
            self.logger.error("No tickers found for screening")
            return []
        
        self.logger.info(f"Screening {len(tickers)} stocks...")
        
        # Screen stocks in batches to avoid overwhelming APIs
        batch_size = 10
        all_results = []
        
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1}/{(len(tickers)-1)//batch_size + 1}")
            
            batch_results = await self._screen_batch(batch)
            all_results.extend(batch_results)
            
            # Rate limiting pause
            if not self.config.dry_run:
                await asyncio.sleep(1)
        
        # Filter and rank results
        qualified_stocks = self._apply_graham_filters(all_results)
        ranked_stocks = self._rank_stocks(qualified_stocks)
        
        # Take top N
        top_stocks = ranked_stocks[:self.config.top_count]
        
        # Generate reports
        if top_stocks:
            await self._generate_reports(top_stocks)
        
        # Cleanup
        await self.data_provider.close()
        
        return top_stocks
    
    async def _get_screening_universe(self) -> List[str]:
        """Get list of tickers to screen"""
        
        if self.config.tickers_csv:
            tickers = self._load_tickers_from_csv()
        elif self.config.universe == 'nyse':
            tickers = await self.data_provider.get_nyse_tickers()
        elif self.config.universe == 'nasdaq':
            # TODO: Implement NASDAQ ticker fetching
            self.logger.warning("NASDAQ universe not implemented, using NYSE")
            tickers = await self.data_provider.get_nyse_tickers()
        elif self.config.universe == 'all':
            # TODO: Implement combined universe
            self.logger.warning("Combined universe not implemented, using NYSE")
            tickers = await self.data_provider.get_nyse_tickers()
        else:
            tickers = []
        
        # Apply random sampling if requested
        if self.config.random_sample and self.config.random_sample < len(tickers):
            original_count = len(tickers)
            tickers = random.sample(tickers, self.config.random_sample)
            self.logger.info(f"Randomly sampled {len(tickers)} stocks from {original_count} total")
        
        return tickers
    
    def _load_tickers_from_csv(self) -> List[str]:
        """Load tickers from CSV file"""
        try:
            df = pd.read_csv(self.config.tickers_csv)
            # Assume first column contains tickers
            return df.iloc[:, 0].str.upper().tolist()
        except Exception as e:
            self.logger.error(f"Error loading tickers from CSV: {str(e)}")
            return []
    
    async def _screen_batch(self, tickers: List[str]) -> List[ScreenResult]:
        """Screen a batch of stocks"""
        
        tasks = [self._screen_single_stock(ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for result in results:
            if isinstance(result, ScreenResult):
                valid_results.append(result)
            elif isinstance(result, Exception):
                self.logger.warning(f"Error screening stock: {str(result)}")
        
        return valid_results
    
    async def _screen_single_stock(self, ticker: str) -> Optional[ScreenResult]:
        """Screen a single stock using Graham criteria"""
        
        try:
            # Get company profile
            profile = await self.data_provider.get_company_profile(ticker)
            if not profile:
                return None
            
            # Apply market cap filter
            if (self.config.min_market_cap and 
                profile.market_cap and 
                profile.market_cap < self.config.min_market_cap):
                return None
            
            # Get financial statements
            statements = await self.data_provider.get_financial_statements(ticker, self.config.years)
            if len(statements) < 15:  # Need at least 5 years × 3 statement types
                self.logger.debug(f"Insufficient financial data for {ticker}")
                return None
            
            # Get current price
            current_price = await self.data_provider.get_stock_price(ticker)
            if not current_price or current_price <= 0:
                return None
            
            # Calculate valuations
            valuations, metrics = self.valuator.calculate_all_valuations(statements, profile, current_price)
            if not valuations:
                return None
            
            # Triangulate intrinsic value
            triangulated_value = self.valuator.triangulate_value(valuations)
            if not triangulated_value:
                return None
            
            # Calculate overall margin of safety
            margin_of_safety = (triangulated_value - current_price) / triangulated_value
            
            # Calculate Graham score
            graham_score = self._calculate_graham_score(metrics, margin_of_safety)
            
            return ScreenResult(
                ticker=ticker,
                company_name=profile.name,
                sector=profile.sector,
                current_price=current_price,
                intrinsic_value=triangulated_value,
                margin_of_safety=margin_of_safety,
                triangulated_value=triangulated_value,
                valuations=valuations,
                metrics=metrics,
                graham_score=graham_score
            )
            
        except Exception as e:
            self.logger.warning(f"Error screening {ticker}: {str(e)}")
            return None
    
    def _apply_graham_filters(self, results: List[ScreenResult]) -> List[ScreenResult]:
        """Apply Benjamin Graham's investment criteria"""
        
        qualified = []
        
        for result in results:
            reasons = []
            
            # 1. Current ratio >= 2.0 (liquidity)
            if not result.metrics.current_ratio or result.metrics.current_ratio < self.config.min_current_ratio:
                reasons.append(f"Current ratio {result.metrics.current_ratio:.2f} < {self.config.min_current_ratio}")
            
            # 2. Debt-to-equity <= 0.5 (conservative leverage)
            if result.metrics.debt_to_equity and result.metrics.debt_to_equity > self.config.max_debt_to_equity:
                reasons.append(f"Debt/equity {result.metrics.debt_to_equity:.2f} > {self.config.max_debt_to_equity}")
            
            # 3. Consistent earnings (positive for required years)
            if not result.metrics.earnings_growth or result.metrics.earnings_growth < 0:
                reasons.append("Inconsistent or negative earnings growth")
            
            # 4. PE ratio <= 15 (not overpaying for earnings)
            if result.metrics.pe_ratio and result.metrics.pe_ratio > self.config.max_pe_ratio:
                reasons.append(f"PE ratio {result.metrics.pe_ratio:.2f} > {self.config.max_pe_ratio}")
            
            # 5. PB ratio <= 1.5 (not overpaying for assets)
            if result.metrics.pb_ratio and result.metrics.pb_ratio > self.config.max_pb_ratio:
                reasons.append(f"PB ratio {result.metrics.pb_ratio:.2f} > {self.config.max_pb_ratio}")
            
            # 6. PE × PB <= 22.5 (Graham's combined metric)
            if (result.metrics.pe_ratio and result.metrics.pb_ratio and 
                result.metrics.pe_ratio * result.metrics.pb_ratio > 22.5):
                reasons.append(f"PE×PB {result.metrics.pe_ratio * result.metrics.pb_ratio:.1f} > 22.5")
            
            # 7. Margin of safety >= 50%
            if result.margin_of_safety < self.config.min_margin_of_safety:
                reasons.append(f"Margin of safety {result.margin_of_safety:.1%} < {self.config.min_margin_of_safety:.1%}")
            
            # 8. Positive book value
            if not result.metrics.book_value_per_share or result.metrics.book_value_per_share <= 0:
                reasons.append("Negative or zero book value")
            
            if not reasons:
                qualified.append(result)
                self.logger.debug(f"{result.ticker} passed all Graham filters")
            else:
                self.logger.debug(f"{result.ticker} failed Graham filters: {'; '.join(reasons)}")
        
        self.logger.info(f"{len(qualified)} stocks passed Graham filters out of {len(results)} analyzed")
        return qualified
    
    def _calculate_graham_score(self, metrics: FinancialMetrics, margin_of_safety: float) -> float:
        """Calculate composite Graham score (0-100)"""
        
        score = 0
        
        # Liquidity score (0-20 points)
        if metrics.current_ratio:
            if metrics.current_ratio >= 3.0:
                score += 20
            elif metrics.current_ratio >= 2.0:
                score += 15
            elif metrics.current_ratio >= 1.5:
                score += 10
            elif metrics.current_ratio >= 1.0:
                score += 5
        
        # Leverage score (0-15 points)
        if metrics.debt_to_equity is not None:
            if metrics.debt_to_equity <= 0.3:
                score += 15
            elif metrics.debt_to_equity <= 0.5:
                score += 10
            elif metrics.debt_to_equity <= 0.7:
                score += 5
        
        # Valuation score (0-25 points)
        if metrics.pe_ratio:
            if metrics.pe_ratio <= 10:
                score += 15
            elif metrics.pe_ratio <= 15:
                score += 10
            elif metrics.pe_ratio <= 20:
                score += 5
        
        if metrics.pb_ratio:
            if metrics.pb_ratio <= 1.0:
                score += 10
            elif metrics.pb_ratio <= 1.5:
                score += 5
        
        # Growth score (0-15 points)
        if metrics.earnings_growth:
            if metrics.earnings_growth >= 0.1:
                score += 15
            elif metrics.earnings_growth >= 0.05:
                score += 10
            elif metrics.earnings_growth > 0:
                score += 5
        
        # Dividend consistency (0-10 points)
        if metrics.dividend_years >= 10:
            score += 10
        elif metrics.dividend_years >= 5:
            score += 5
        
        # Margin of safety bonus (0-15 points)
        if margin_of_safety >= 0.7:
            score += 15
        elif margin_of_safety >= 0.5:
            score += 10
        elif margin_of_safety >= 0.3:
            score += 5
        
        return min(score, 100)  # Cap at 100
    
    def _rank_stocks(self, stocks: List[ScreenResult]) -> List[ScreenResult]:
        """Rank stocks by Graham score and margin of safety"""
        
        # Primary sort: Graham score (descending)
        # Secondary sort: Margin of safety (descending)
        sorted_stocks = sorted(
            stocks, 
            key=lambda x: (x.graham_score, x.margin_of_safety), 
            reverse=True
        )
        
        # Assign ranks
        for i, stock in enumerate(sorted_stocks):
            stock.rank = i + 1
        
        return sorted_stocks
    
    async def _generate_reports(self, stocks: List[ScreenResult]):
        """Generate output reports"""
        
        # Generate summary CSV
        await self._generate_summary_csv(stocks)
        
        # Generate summary JSON
        await self._generate_summary_json(stocks)
        
        # Generate individual company reports
        for stock in stocks:
            await self.report_generator.generate_company_report(stock)
    
    async def _generate_summary_csv(self, stocks: List[ScreenResult]):
        """Generate top stocks summary CSV"""
        
        data = []
        for stock in stocks:
            data.append({
                'Rank': stock.rank,
                'Ticker': stock.ticker,
                'Company': stock.company_name,
                'Sector': stock.sector,
                'Current Price': f"${stock.current_price:.2f}",
                'Intrinsic Value': f"${stock.intrinsic_value:.2f}",
                'Margin of Safety': f"{stock.margin_of_safety:.1%}",
                'Graham Score': f"{stock.graham_score:.1f}",
                'Current Ratio': f"{stock.metrics.current_ratio:.2f}" if stock.metrics.current_ratio else 'N/A',
                'Debt/Equity': f"{stock.metrics.debt_to_equity:.2f}" if stock.metrics.debt_to_equity else 'N/A',
                'PE Ratio': f"{stock.metrics.pe_ratio:.2f}" if stock.metrics.pe_ratio else 'N/A',
                'PB Ratio': f"{stock.metrics.pb_ratio:.2f}" if stock.metrics.pb_ratio else 'N/A',
                'ROE': f"{stock.metrics.roe:.1%}" if stock.metrics.roe else 'N/A'
            })
        
        df = pd.DataFrame(data)
        output_path = self.config.output_dir / 'top_10.csv'
        df.to_csv(output_path, index=False)
        self.logger.info(f"Summary CSV saved to {output_path}")
    
    async def _generate_summary_json(self, stocks: List[ScreenResult]):
        """Generate top stocks summary JSON"""
        
        summary = {
            'screen_date': datetime.now().isoformat(),
            'config': {
                'universe': self.config.universe,
                'top_count': self.config.top_count,
                'years': self.config.years,
                'min_margin_of_safety': self.config.min_margin_of_safety
            },
            'stocks': [stock.to_dict() for stock in stocks]
        }
        
        output_path = self.config.output_dir / 'top_10.json'
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.logger.info(f"Summary JSON saved to {output_path}")