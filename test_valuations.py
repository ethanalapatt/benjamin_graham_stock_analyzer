"""Unit tests for Graham valuation calculators"""

import pytest
from datetime import datetime
from unittest.mock import Mock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import Config
from src.valuations import GrahamValuator, FinancialMetrics
from src.data_providers import FinancialStatement, CompanyProfile


class TestGrahamValuator:
    """Test Benjamin Graham valuation methods"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return Config(
            capex_multiplier=1.2,
            depreciation_conservatism=1.1,
            working_capital_adjustment=0.9
        )
    
    @pytest.fixture
    def valuator(self, config):
        """Graham valuator instance"""
        return GrahamValuator(config)
    
    @pytest.fixture
    def sample_profile(self):
        """Sample company profile"""
        return CompanyProfile(
            ticker="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            market_cap=1000000000
        )
    
    @pytest.fixture
    def sample_statements(self):
        """Sample financial statements for testing"""
        statements = []
        
        # Create 3 years of financial statements
        for year in [2023, 2022, 2021]:
            # Income statement
            income_data = {
                'fiscalDateEnding': f'{year}-12-31',
                'netIncome': '100000000',  # $100M
                'depreciationAndAmortization': '20000000'  # $20M
            }
            statements.append(FinancialStatement(
                ticker="TEST",
                year=year,
                statement_type='income',
                data=income_data,
                filing_date=datetime(year, 12, 31)
            ))
            
            # Balance sheet
            balance_data = {
                'fiscalDateEnding': f'{year}-12-31',
                'totalCurrentAssets': '500000000',  # $500M
                'totalCurrentLiabilities': '200000000',  # $200M
                'totalStockholderEquity': '800000000',  # $800M
                'shortTermDebt': '50000000',  # $50M
                'longTermDebt': '150000000',  # $150M
                'commonStockSharesOutstanding': '50000000',  # 50M shares
                'intangibleAssets': '100000000',  # $100M
                'goodwill': '50000000',  # $50M
                'totalLiabilities': '400000000'  # $400M
            }
            statements.append(FinancialStatement(
                ticker="TEST",
                year=year,
                statement_type='balance',
                data=balance_data,
                filing_date=datetime(year, 12, 31)
            ))
            
            # Cash flow statement
            cash_flow_data = {
                'fiscalDateEnding': f'{year}-12-31',
                'operatingCashflow': '120000000',  # $120M
                'capitalExpenditures': '-30000000',  # $30M outflow
                'dividendsPaid': '-20000000'  # $20M dividends
            }
            statements.append(FinancialStatement(
                ticker="TEST",
                year=year,
                statement_type='cash_flow',
                data=cash_flow_data,
                filing_date=datetime(year, 12, 31)
            ))
        
        return statements
    
    def test_calculate_financial_metrics(self, valuator, sample_statements, sample_profile):
        """Test financial metrics calculation"""
        current_price = 20.0
        
        metrics = valuator._calculate_financial_metrics(
            sample_statements, sample_profile, current_price
        )
        
        assert metrics.ticker == "TEST"
        assert metrics.current_ratio == 2.5  # 500M / 200M
        assert metrics.debt_to_equity == 0.25  # (50M + 150M) / 800M
        assert metrics.book_value_per_share == 16.0  # 800M / 50M shares
        assert metrics.pe_ratio == 10.0  # $20 / ($100M / 50M shares)
        assert metrics.pb_ratio == 1.25  # $20 / $16
        assert metrics.roe == 0.125  # 100M / 800M
        
        # NCAV per share: (500M - 400M) / 50M = $2.00
        assert metrics.ncav_per_share == 2.0
        
        # Tangible book value: (800M - 100M - 50M) / 50M = $13.00
        assert metrics.tangible_book_value == 13.0
    
    def test_calculate_owner_earnings(self, valuator, sample_statements):
        """Test owner earnings calculation with conservative adjustments"""
        
        # Group statements by type
        by_type = {}
        for stmt in sample_statements:
            if stmt.statement_type not in by_type:
                by_type[stmt.statement_type] = {}
            by_type[stmt.statement_type][stmt.year] = stmt
        
        owner_earnings = valuator._calculate_owner_earnings(by_type, 2023)
        
        # Operating CF: $120M
        # Capex (with 20% conservatism): $30M * 1.2 = $36M
        # Owner earnings: $120M - $36M = $84M
        assert owner_earnings == 84000000
    
    def test_calculate_earnings_growth(self, valuator):
        """Test earnings growth calculation"""
        
        # Mock income statements with consistent $100M earnings
        by_type = {'income': {}}
        for year in [2021, 2022, 2023]:
            mock_stmt = Mock()
            mock_stmt.data = {'netIncome': '100000000'}
            by_type['income'][year] = mock_stmt
        
        growth = valuator._calculate_earnings_growth(by_type)
        
        # With flat earnings, growth should be 0
        assert growth == 0.0
        
        # Test with 10% growth
        by_type['income'][2021].data = {'netIncome': '82644628'}  # ~10% CAGR to 100M
        by_type['income'][2022].data = {'netIncome': '90909091'}
        by_type['income'][2023].data = {'netIncome': '100000000'}
        
        growth = valuator._calculate_earnings_growth(by_type)
        assert abs(growth - 0.1) < 0.01  # Within 1% of 10%
    
    def test_calculate_epv(self, valuator, sample_statements, sample_profile):
        """Test Earnings Power Value calculation"""
        
        current_price = 20.0
        
        # Calculate metrics first
        metrics = valuator._calculate_financial_metrics(
            sample_statements, sample_profile, current_price
        )
        
        epv_result = valuator._calculate_epv(sample_statements, current_price, metrics)
        
        assert epv_result is not None
        assert epv_result.method == "Earnings Power Value (EPV)"
        
        # Owner earnings: $84M (from test above)
        # Shares: 50M
        # Owner earnings per share: $84M / 50M = $1.68
        # EPV per share: $1.68 / 0.10 = $16.80
        expected_epv = 1.68 / 0.10
        assert abs(epv_result.intrinsic_value - expected_epv) < 0.01
        
        # Margin of safety: (16.80 - 20.00) / 16.80 = negative
        assert epv_result.margin_of_safety < 0
    
    def test_calculate_asset_value(self, valuator, sample_statements, sample_profile):
        """Test asset-based valuation"""
        
        current_price = 20.0
        
        metrics = valuator._calculate_financial_metrics(
            sample_statements, sample_profile, current_price
        )
        
        asset_result = valuator._calculate_asset_value(sample_statements, current_price, metrics)
        
        assert asset_result is not None
        assert asset_result.method == "Asset-Based Valuation"
        
        # Should use NCAV ($2.00 per share) since it's positive
        assert asset_result.intrinsic_value == 2.0
        
        # Margin of safety: (2.00 - 20.00) / 2.00 = very negative
        assert asset_result.margin_of_safety < -5
    
    def test_calculate_conservative_dcf(self, valuator, sample_statements, sample_profile):
        """Test conservative DCF calculation"""
        
        current_price = 20.0
        
        metrics = valuator._calculate_financial_metrics(
            sample_statements, sample_profile, current_price
        )
        
        # Set a mock growth rate
        metrics.earnings_growth = 0.05  # 5% growth
        
        dcf_result = valuator._calculate_conservative_dcf(sample_statements, current_price, metrics)
        
        assert dcf_result is not None
        assert dcf_result.method == "Conservative DCF"
        
        # DCF should be higher than EPV due to growth assumptions
        assert dcf_result.intrinsic_value > 16.80
        
        # Should have conservative assumptions
        assert any("5%" in assumption for assumption in dcf_result.assumptions)
    
    def test_triangulate_value(self, valuator):
        """Test value triangulation with multiple methods"""
        
        from src.valuations import ValuationResult
        
        valuations = [
            ValuationResult("EPV", 16.80, 20.0, -0.19, "high", [], []),
            ValuationResult("Asset", 2.0, 20.0, -9.0, "medium", [], []),
            ValuationResult("DCF", 25.0, 20.0, 0.2, "low", [], [])
        ]
        
        triangulated = valuator.triangulate_value(valuations)
        
        # Should weight by confidence: high=3, medium=2, low=1
        # (16.80*3 + 2.0*2 + 25.0*1) / (3+2+1) = 79.4 / 6 = 13.23
        expected = (16.80 * 3 + 2.0 * 2 + 25.0 * 1) / 6
        assert abs(triangulated - expected) < 0.01
    
    def test_safe_float_conversion(self, valuator):
        """Test safe float conversion utility"""
        
        assert valuator._safe_float("123.45") == 123.45
        assert valuator._safe_float(None) is None
        assert valuator._safe_float("") is None
        assert valuator._safe_float("invalid") is None
        assert valuator._safe_float(0) == 0.0
        assert valuator._safe_float(42) == 42.0
    
    def test_count_dividend_years(self, valuator, sample_statements):
        """Test dividend year counting"""
        
        # Group statements by type
        by_type = {}
        for stmt in sample_statements:
            if stmt.statement_type not in by_type:
                by_type[stmt.statement_type] = {}
            by_type[stmt.statement_type][stmt.year] = stmt
        
        dividend_years = valuator._count_dividend_years(by_type)
        
        # All 3 years have dividends paid (-20M each year)
        assert dividend_years == 3


if __name__ == "__main__":
    pytest.main([__file__])