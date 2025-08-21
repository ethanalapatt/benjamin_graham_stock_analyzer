"""Unit tests for Graham screener"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import Config
from src.screener import GrahamScreener, ScreenResult
from src.valuations import FinancialMetrics, ValuationResult
from src.data_providers import CompanyProfile


class TestGrahamScreener:
    """Test Graham screening logic"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return Config(
            top_count=5,
            min_current_ratio=2.0,
            max_debt_to_equity=0.5,
            max_pe_ratio=15.0,
            max_pb_ratio=1.5,
            min_margin_of_safety=0.5
        )
    
    @pytest.fixture
    def mock_data_provider(self):
        """Mock data provider"""
        provider = Mock()
        provider.get_nyse_tickers = AsyncMock(return_value=['AAPL', 'MSFT', 'GOOGL'])
        provider.get_company_profile = AsyncMock()
        provider.get_financial_statements = AsyncMock()
        provider.get_stock_price = AsyncMock()
        return provider
    
    @pytest.fixture
    def screener(self, config, mock_data_provider):
        """Graham screener instance"""
        return GrahamScreener(config, mock_data_provider)
    
    @pytest.fixture
    def sample_metrics_good(self):
        """Sample metrics that pass Graham filters"""
        return FinancialMetrics(
            ticker="GOOD",
            current_ratio=2.5,
            debt_to_equity=0.3,
            pe_ratio=12.0,
            pb_ratio=1.2,
            book_value_per_share=20.0,
            earnings_growth=0.08,
            dividend_years=10,
            roe=0.15,
            earnings_per_share=2.0,
            owner_earnings=100000000
        )
    
    @pytest.fixture
    def sample_metrics_bad(self):
        """Sample metrics that fail Graham filters"""
        return FinancialMetrics(
            ticker="BAD",
            current_ratio=1.2,  # Fails current ratio test
            debt_to_equity=0.8,  # Fails debt test
            pe_ratio=25.0,  # Fails PE test
            pb_ratio=2.0,  # Fails PB test
            book_value_per_share=10.0,
            earnings_growth=-0.05,  # Negative growth
            dividend_years=0,
            roe=0.05,
            earnings_per_share=1.0,
            owner_earnings=50000000
        )
    
    def test_calculate_graham_score_excellent(self, screener, sample_metrics_good):
        """Test Graham score calculation for excellent stock"""
        
        margin_of_safety = 0.6  # 60% margin
        score = screener._calculate_graham_score(sample_metrics_good, margin_of_safety)
        
        # Should score high across all categories
        assert score >= 80  # Excellent score
        assert score <= 100
    
    def test_calculate_graham_score_poor(self, screener, sample_metrics_bad):
        """Test Graham score calculation for poor stock"""
        
        margin_of_safety = 0.1  # 10% margin (low)
        score = screener._calculate_graham_score(sample_metrics_bad, margin_of_safety)
        
        # Should score poorly due to failing multiple criteria
        assert score <= 40  # Poor score
    
    def test_apply_graham_filters_pass(self, screener, sample_metrics_good):
        """Test Graham filters with passing stock"""
        
        valuations = [
            ValuationResult("EPV", 30.0, 20.0, 0.33, "high", [], [])
        ]
        
        result = ScreenResult(
            ticker="GOOD",
            company_name="Good Company",
            sector="Technology",
            current_price=20.0,
            intrinsic_value=30.0,
            margin_of_safety=0.6,  # 60% margin - passes
            triangulated_value=30.0,
            valuations=valuations,
            metrics=sample_metrics_good,
            graham_score=85.0
        )
        
        qualified = screener._apply_graham_filters([result])
        
        assert len(qualified) == 1
        assert qualified[0].ticker == "GOOD"
    
    def test_apply_graham_filters_fail(self, screener, sample_metrics_bad):
        """Test Graham filters with failing stock"""
        
        valuations = [
            ValuationResult("EPV", 15.0, 20.0, -0.33, "medium", [], [])
        ]
        
        result = ScreenResult(
            ticker="BAD",
            company_name="Bad Company",
            sector="Technology",
            current_price=20.0,
            intrinsic_value=15.0,
            margin_of_safety=0.1,  # 10% margin - fails
            triangulated_value=15.0,
            valuations=valuations,
            metrics=sample_metrics_bad,
            graham_score=30.0
        )
        
        qualified = screener._apply_graham_filters([result])
        
        # Should fail multiple filters
        assert len(qualified) == 0
    
    def test_apply_graham_pe_pb_combination(self, screener):
        """Test Graham's PE × PB <= 22.5 rule"""
        
        # Create metrics that pass individual PE and PB tests but fail combination
        metrics = FinancialMetrics(
            ticker="COMBO",
            current_ratio=2.5,
            debt_to_equity=0.3,
            pe_ratio=14.0,  # Passes PE test (< 15)
            pb_ratio=2.0,   # Fails PB test (> 1.5) 
            book_value_per_share=10.0,
            earnings_growth=0.05,
            dividend_years=5,
            roe=0.12
        )
        
        # PE × PB = 14.0 × 2.0 = 28.0 > 22.5 (should fail)
        
        valuations = [ValuationResult("EPV", 25.0, 20.0, 0.2, "high", [], [])]
        
        result = ScreenResult(
            ticker="COMBO",
            company_name="Combo Test",
            sector="Technology", 
            current_price=20.0,
            intrinsic_value=25.0,
            margin_of_safety=0.6,
            triangulated_value=25.0,
            valuations=valuations,
            metrics=metrics,
            graham_score=70.0
        )
        
        qualified = screener._apply_graham_filters([result])
        
        # Should fail due to PE × PB > 22.5
        assert len(qualified) == 0
    
    def test_rank_stocks(self, screener):
        """Test stock ranking logic"""
        
        # Create stocks with different scores
        stocks = []
        
        for i, (score, margin) in enumerate([(90, 0.7), (85, 0.6), (80, 0.8)]):
            metrics = FinancialMetrics(ticker=f"STOCK{i}")
            valuations = [ValuationResult("EPV", 25.0, 20.0, margin, "high", [], [])]
            
            stock = ScreenResult(
                ticker=f"STOCK{i}",
                company_name=f"Company {i}",
                sector="Technology",
                current_price=20.0,
                intrinsic_value=25.0,
                margin_of_safety=margin,
                triangulated_value=25.0,
                valuations=valuations,
                metrics=metrics,
                graham_score=score
            )
            stocks.append(stock)
        
        ranked = screener._rank_stocks(stocks)
        
        # Should be ranked by Graham score first, then margin of safety
        assert ranked[0].graham_score == 90  # Highest score
        assert ranked[1].graham_score == 85  
        assert ranked[2].graham_score == 80  # Lowest score despite highest margin
        
        # Check ranks are assigned
        assert ranked[0].rank == 1
        assert ranked[1].rank == 2
        assert ranked[2].rank == 3
    
    def test_load_tickers_from_csv(self, screener, tmp_path):
        """Test loading tickers from CSV file"""
        
        # Create test CSV
        csv_file = tmp_path / "test_tickers.csv"
        csv_content = "ticker,name\nAAPL,Apple Inc\nMSFT,Microsoft\ngoogl,Alphabet"
        csv_file.write_text(csv_content)
        
        # Update config to use test CSV
        screener.config.tickers_csv = str(csv_file)
        
        tickers = screener._load_tickers_from_csv()
        
        assert len(tickers) == 3
        assert "AAPL" in tickers
        assert "MSFT" in tickers
        assert "GOOGL" in tickers  # Should be uppercase
    
    @pytest.mark.asyncio
    async def test_get_screening_universe_nyse(self, screener, mock_data_provider):
        """Test getting NYSE universe"""
        
        tickers = await screener._get_screening_universe()
        
        mock_data_provider.get_nyse_tickers.assert_called_once()
        assert tickers == ['AAPL', 'MSFT', 'GOOGL']
    
    def test_margin_of_safety_edge_cases(self, screener):
        """Test margin of safety edge cases"""
        
        # Test with zero intrinsic value
        metrics = FinancialMetrics(ticker="ZERO")
        valuations = [ValuationResult("EPV", 0.0, 20.0, -1.0, "low", [], [])]
        
        result = ScreenResult(
            ticker="ZERO",
            company_name="Zero Value",
            sector="Technology",
            current_price=20.0,
            intrinsic_value=0.0,
            margin_of_safety=-1.0,
            triangulated_value=0.0,
            valuations=valuations,
            metrics=metrics,
            graham_score=0.0
        )
        
        qualified = screener._apply_graham_filters([result])
        assert len(qualified) == 0  # Should fail margin of safety test
    
    def test_negative_book_value_filter(self, screener):
        """Test filtering stocks with negative book value"""
        
        metrics = FinancialMetrics(
            ticker="NEGATIVE",
            current_ratio=3.0,
            debt_to_equity=0.2,
            pe_ratio=10.0,
            pb_ratio=1.0,
            book_value_per_share=-5.0,  # Negative book value
            earnings_growth=0.05,
            dividend_years=10,
            roe=0.15
        )
        
        valuations = [ValuationResult("EPV", 25.0, 20.0, 0.2, "high", [], [])]
        
        result = ScreenResult(
            ticker="NEGATIVE",
            company_name="Negative Book Value",
            sector="Technology",
            current_price=20.0,
            intrinsic_value=25.0,
            margin_of_safety=0.6,
            triangulated_value=25.0,
            valuations=valuations,
            metrics=metrics,
            graham_score=70.0
        )
        
        qualified = screener._apply_graham_filters([result])
        
        # Should fail due to negative book value
        assert len(qualified) == 0


if __name__ == "__main__":
    pytest.main([__file__])