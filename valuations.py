"""Benjamin Graham valuation methods implementation"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np

from .data_providers import FinancialStatement, CompanyProfile
from .config import Config


@dataclass
class ValuationResult:
    method: str
    intrinsic_value: float
    current_price: float
    margin_of_safety: float
    confidence: str  # 'high', 'medium', 'low'
    assumptions: List[str]
    warnings: List[str]


@dataclass
class FinancialMetrics:
    ticker: str
    current_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    roe: Optional[float] = None
    earnings_growth: Optional[float] = None
    dividend_years: int = 0
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    book_value_per_share: Optional[float] = None
    earnings_per_share: Optional[float] = None
    owner_earnings: Optional[float] = None
    ncav_per_share: Optional[float] = None
    tangible_book_value: Optional[float] = None


class GrahamValuator:
    """Benjamin Graham valuation methods with conservative assumptions"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def calculate_all_valuations(
        self, 
        statements: List[FinancialStatement], 
        profile: CompanyProfile,
        current_price: float
    ) -> Tuple[List[ValuationResult], FinancialMetrics]:
        """Calculate all Graham valuation methods"""
        
        metrics = self._calculate_financial_metrics(statements, profile, current_price)
        valuations = []
        
        # 1. Earnings Power Value (EPV)
        epv_result = self._calculate_epv(statements, current_price, metrics)
        if epv_result:
            valuations.append(epv_result)
        
        # 2. Asset-based valuation (NCAV and TBV)
        asset_result = self._calculate_asset_value(statements, current_price, metrics)
        if asset_result:
            valuations.append(asset_result)
        
        # 3. Conservative DCF
        dcf_result = self._calculate_conservative_dcf(statements, current_price, metrics)
        if dcf_result:
            valuations.append(dcf_result)
        
        return valuations, metrics
    
    def _calculate_financial_metrics(
        self, 
        statements: List[FinancialStatement], 
        profile: CompanyProfile,
        current_price: float
    ) -> FinancialMetrics:
        """Calculate key financial metrics for Graham screening"""
        
        metrics = FinancialMetrics(ticker=profile.ticker)
        
        # Group statements by type and year
        by_type = {}
        for stmt in statements:
            if stmt.statement_type not in by_type:
                by_type[stmt.statement_type] = {}
            by_type[stmt.statement_type][stmt.year] = stmt
        
        # Get latest year data
        latest_year = max(stmt.year for stmt in statements) if statements else None
        if not latest_year:
            return metrics
        
        # Current ratio (Current Assets / Current Liabilities)
        balance_latest = by_type.get('balance', {}).get(latest_year)
        if balance_latest:
            current_assets = self._safe_float(balance_latest.data.get('totalCurrentAssets'))
            current_liabilities = self._safe_float(balance_latest.data.get('totalCurrentLiabilities'))
            if current_assets and current_liabilities and current_liabilities > 0:
                metrics.current_ratio = current_assets / current_liabilities
        
        # Debt to equity
        if balance_latest:
            total_debt = (
                self._safe_float(balance_latest.data.get('shortTermDebt', 0)) +
                self._safe_float(balance_latest.data.get('longTermDebt', 0))
            )
            total_equity = self._safe_float(balance_latest.data.get('totalStockholderEquity'))
            if total_equity and total_equity > 0:
                metrics.debt_to_equity = total_debt / total_equity
        
        # Book value per share
        if balance_latest:
            book_value = self._safe_float(balance_latest.data.get('totalStockholderEquity'))
            shares = self._safe_float(balance_latest.data.get('commonStockSharesOutstanding'))
            if book_value and shares and shares > 0:
                metrics.book_value_per_share = book_value / shares
        
        # Calculate NCAV per share (Net Current Asset Value)
        if balance_latest:
            current_assets = self._safe_float(balance_latest.data.get('totalCurrentAssets', 0))
            total_liabilities = self._safe_float(balance_latest.data.get('totalLiabilities', 0))
            shares = self._safe_float(balance_latest.data.get('commonStockSharesOutstanding'))
            
            if current_assets and total_liabilities is not None and shares and shares > 0:
                ncav = current_assets - total_liabilities
                metrics.ncav_per_share = ncav / shares
        
        # Tangible book value (remove intangibles)
        if balance_latest:
            book_value = self._safe_float(balance_latest.data.get('totalStockholderEquity', 0))
            intangibles = self._safe_float(balance_latest.data.get('intangibleAssets', 0))
            goodwill = self._safe_float(balance_latest.data.get('goodwill', 0))
            shares = self._safe_float(balance_latest.data.get('commonStockSharesOutstanding'))
            
            if book_value is not None and shares and shares > 0:
                tangible_bv = book_value - (intangibles or 0) - (goodwill or 0)
                metrics.tangible_book_value = tangible_bv / shares
        
        # Earnings per share and PE ratio
        income_latest = by_type.get('income', {}).get(latest_year)
        if income_latest and balance_latest:
            net_income = self._safe_float(income_latest.data.get('netIncome'))
            shares = self._safe_float(balance_latest.data.get('commonStockSharesOutstanding'))
            
            if net_income and shares and shares > 0:
                metrics.earnings_per_share = net_income / shares
                if metrics.earnings_per_share > 0:
                    metrics.pe_ratio = current_price / metrics.earnings_per_share
        
        # PB ratio
        if metrics.book_value_per_share and metrics.book_value_per_share > 0:
            metrics.pb_ratio = current_price / metrics.book_value_per_share
        
        # Calculate owner earnings (Buffett/Graham approach)
        metrics.owner_earnings = self._calculate_owner_earnings(by_type, latest_year)
        
        # ROE calculation
        if income_latest and balance_latest:
            net_income = self._safe_float(income_latest.data.get('netIncome'))
            equity = self._safe_float(balance_latest.data.get('totalStockholderEquity'))
            if net_income and equity and equity > 0:
                metrics.roe = net_income / equity
        
        # Earnings growth over time
        metrics.earnings_growth = self._calculate_earnings_growth(by_type)
        
        # Count dividend-paying years
        metrics.dividend_years = self._count_dividend_years(by_type)
        
        return metrics
    
    def _calculate_owner_earnings(self, by_type: Dict, latest_year: int) -> Optional[float]:
        """Calculate owner earnings with conservative adjustments"""
        
        cash_flow_latest = by_type.get('cash_flow', {}).get(latest_year)
        if not cash_flow_latest:
            return None
        
        # Start with operating cash flow
        operating_cf = self._safe_float(cash_flow_latest.data.get('operatingCashflow'))
        if not operating_cf:
            return None
        
        # Subtract maintenance capex (conservatively estimated)
        capex = self._safe_float(cash_flow_latest.data.get('capitalExpenditures', 0))
        if capex:
            # Apply conservative multiplier to capex
            maintenance_capex = abs(capex) * self.config.capex_multiplier
            owner_earnings = operating_cf - maintenance_capex
        else:
            # If no capex data, use depreciation as proxy and add conservatism
            income_latest = by_type.get('income', {}).get(latest_year)
            if income_latest:
                depreciation = self._safe_float(income_latest.data.get('depreciationAndAmortization', 0))
                if depreciation:
                    maintenance_capex = depreciation * self.config.depreciation_conservatism
                    owner_earnings = operating_cf - maintenance_capex
                else:
                    # Very conservative estimate: 20% of operating CF for maintenance
                    owner_earnings = operating_cf * 0.8
            else:
                owner_earnings = operating_cf * 0.8
        
        return owner_earnings if owner_earnings > 0 else None
    
    def _calculate_earnings_growth(self, by_type: Dict) -> Optional[float]:
        """Calculate compound annual growth rate of earnings"""
        
        income_statements = by_type.get('income', {})
        years = sorted(income_statements.keys())
        
        if len(years) < 3:
            return None
        
        earnings = []
        for year in years:
            net_income = self._safe_float(income_statements[year].data.get('netIncome'))
            if net_income and net_income > 0:
                earnings.append(net_income)
            else:
                return None  # Graham requires consistent positive earnings
        
        if len(earnings) < 3:
            return None
        
        # Calculate CAGR
        start_earnings = earnings[0]
        end_earnings = earnings[-1]
        years_span = len(earnings) - 1
        
        if start_earnings > 0:
            cagr = (end_earnings / start_earnings) ** (1 / years_span) - 1
            return cagr
        
        return None
    
    def _count_dividend_years(self, by_type: Dict) -> int:
        """Count years with dividend payments"""
        
        cash_flow_statements = by_type.get('cash_flow', {})
        dividend_years = 0
        
        for year, stmt in cash_flow_statements.items():
            dividends = self._safe_float(stmt.data.get('dividendsPaid', 0))
            if dividends and dividends < 0:  # Dividends are negative in cash flow
                dividend_years += 1
        
        return dividend_years
    
    def _calculate_epv(
        self, 
        statements: List[FinancialStatement], 
        current_price: float,
        metrics: FinancialMetrics
    ) -> Optional[ValuationResult]:
        """Calculate Earnings Power Value"""
        
        if not metrics.owner_earnings or not metrics.book_value_per_share:
            return None
        
        # Use 10% discount rate (Graham's conservative approach)
        discount_rate = 0.10
        
        # EPV = Owner Earnings / Discount Rate (no growth assumption)
        shares_outstanding = None
        for stmt in statements:
            if stmt.statement_type == 'balance':
                shares = self._safe_float(stmt.data.get('commonStockSharesOutstanding'))
                if shares:
                    shares_outstanding = shares
                    break
        
        if not shares_outstanding:
            return None
        
        owner_earnings_per_share = metrics.owner_earnings / shares_outstanding
        epv_per_share = owner_earnings_per_share / discount_rate
        
        margin_of_safety = (epv_per_share - current_price) / epv_per_share if epv_per_share > 0 else -1
        
        assumptions = [
            f"10% discount rate used",
            f"No growth assumed (conservative)",
            f"Owner earnings: ${metrics.owner_earnings:,.0f}",
            f"Capex multiplier: {self.config.capex_multiplier}"
        ]
        
        warnings = []
        confidence = 'high'
        
        if margin_of_safety < 0.3:
            warnings.append("Margin of safety below 30%")
            confidence = 'medium'
        
        if not metrics.current_ratio or metrics.current_ratio < 2.0:
            warnings.append("Current ratio below 2.0")
            confidence = 'medium'
        
        return ValuationResult(
            method="Earnings Power Value (EPV)",
            intrinsic_value=epv_per_share,
            current_price=current_price,
            margin_of_safety=margin_of_safety,
            confidence=confidence,
            assumptions=assumptions,
            warnings=warnings
        )
    
    def _calculate_asset_value(
        self, 
        statements: List[FinancialStatement], 
        current_price: float,
        metrics: FinancialMetrics
    ) -> Optional[ValuationResult]:
        """Calculate asset-based valuation using NCAV and TBV"""
        
        assumptions = []
        warnings = []
        confidence = 'medium'
        
        # Prefer NCAV if available and positive
        if metrics.ncav_per_share and metrics.ncav_per_share > 0:
            intrinsic_value = metrics.ncav_per_share
            assumptions.append("Using Net Current Asset Value (NCAV)")
            assumptions.append("All current assets at full value")
            assumptions.append("All liabilities at face value")
            confidence = 'high'  # NCAV is very conservative
        elif metrics.tangible_book_value and metrics.tangible_book_value > 0:
            # Use tangible book value with haircut
            intrinsic_value = metrics.tangible_book_value * 0.8  # 20% haircut
            assumptions.append("Using Tangible Book Value with 20% haircut")
            assumptions.append("Excludes goodwill and intangibles")
            warnings.append("Assuming 20% haircut on tangible assets")
        else:
            return None
        
        margin_of_safety = (intrinsic_value - current_price) / intrinsic_value if intrinsic_value > 0 else -1
        
        if margin_of_safety < 0.5:
            warnings.append("Graham prefers 50%+ margin for asset plays")
            confidence = 'low'
        
        return ValuationResult(
            method="Asset-Based Valuation",
            intrinsic_value=intrinsic_value,
            current_price=current_price,
            margin_of_safety=margin_of_safety,
            confidence=confidence,
            assumptions=assumptions,
            warnings=warnings
        )
    
    def _calculate_conservative_dcf(
        self, 
        statements: List[FinancialStatement], 
        current_price: float,
        metrics: FinancialMetrics
    ) -> Optional[ValuationResult]:
        """Conservative DCF with Graham principles"""
        
        if not metrics.owner_earnings or not metrics.earnings_growth:
            return None
        
        # Very conservative growth assumptions
        growth_rate = min(metrics.earnings_growth, 0.05)  # Cap at 5%
        if growth_rate < 0:
            growth_rate = 0  # No negative growth in valuation
        
        # Terminal growth rate (very conservative)
        terminal_growth = min(growth_rate * 0.5, 0.02)  # Max 2%
        
        # Discount rate (higher than EPV for growth assumptions)
        discount_rate = 0.12
        
        assumptions = [
            f"Growth rate: {growth_rate:.1%} (capped at 5%)",
            f"Terminal growth: {terminal_growth:.1%}",
            f"Discount rate: {discount_rate:.1%}",
            "10-year projection period"
        ]
        
        # Project cash flows for 10 years
        current_earnings = metrics.owner_earnings
        present_value = 0
        
        for year in range(1, 11):
            future_earnings = current_earnings * ((1 + growth_rate) ** year)
            pv = future_earnings / ((1 + discount_rate) ** year)
            present_value += pv
        
        # Terminal value
        terminal_earnings = current_earnings * ((1 + growth_rate) ** 10)
        terminal_value = terminal_earnings * (1 + terminal_growth) / (discount_rate - terminal_growth)
        terminal_pv = terminal_value / ((1 + discount_rate) ** 10)
        
        total_value = present_value + terminal_pv
        
        # Get shares outstanding
        shares_outstanding = None
        for stmt in statements:
            if stmt.statement_type == 'balance':
                shares = self._safe_float(stmt.data.get('commonStockSharesOutstanding'))
                if shares:
                    shares_outstanding = shares
                    break
        
        if not shares_outstanding:
            return None
        
        dcf_per_share = total_value / shares_outstanding
        margin_of_safety = (dcf_per_share - current_price) / dcf_per_share if dcf_per_share > 0 else -1
        
        warnings = []
        confidence = 'low'  # DCF is inherently uncertain
        
        if growth_rate > 0.03:
            warnings.append("Growth rate above 3% increases uncertainty")
        
        if margin_of_safety < 0.5:
            warnings.append("Graham requires large margin for growth assumptions")
        
        return ValuationResult(
            method="Conservative DCF",
            intrinsic_value=dcf_per_share,
            current_price=current_price,
            margin_of_safety=margin_of_safety,
            confidence=confidence,
            assumptions=assumptions,
            warnings=warnings
        )
    
    def triangulate_value(self, valuations: List[ValuationResult]) -> Optional[float]:
        """Triangulate intrinsic value from multiple methods"""
        
        if not valuations:
            return None
        
        # Weight by confidence
        weights = {'high': 3, 'medium': 2, 'low': 1}
        
        weighted_sum = 0
        total_weight = 0
        
        for val in valuations:
            weight = weights.get(val.confidence, 1)
            weighted_sum += val.intrinsic_value * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else None
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None