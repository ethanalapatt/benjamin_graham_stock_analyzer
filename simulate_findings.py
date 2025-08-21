#!/usr/bin/env python3
"""
Simulate the Graham screener finding qualifying value stocks
Shows what the output would look like when value stocks are found
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from src.config import Config
from src.screener import ScreenResult
from src.valuations import FinancialMetrics, ValuationResult
from src.reports import ReportGenerator


def create_sample_value_stock():
    """Create a sample stock that would pass Graham's criteria"""
    
    # Sample metrics for a hypothetical value stock
    metrics = FinancialMetrics(
        ticker="VALUE",
        current_ratio=2.8,  # Strong liquidity
        debt_to_equity=0.3,  # Conservative debt
        pe_ratio=8.5,  # Low PE
        pb_ratio=0.9,  # Trading below book value
        book_value_per_share=22.50,
        earnings_per_share=2.35,
        owner_earnings=45000000,
        roe=0.18,  # Good ROE
        earnings_growth=0.06,  # Steady growth
        dividend_years=12,  # Long dividend history
        ncav_per_share=5.50,  # Positive net current assets
        tangible_book_value=20.00
    )
    
    # Sample valuations
    valuations = [
        ValuationResult(
            method="Earnings Power Value (EPV)",
            intrinsic_value=28.20,
            current_price=17.50,
            margin_of_safety=0.38,  # 38% margin
            confidence="high",
            assumptions=[
                "10% discount rate used",
                "No growth assumed (conservative)",
                "Owner earnings: $45,000,000",
                "Capex multiplier: 1.2"
            ],
            warnings=[]
        ),
        ValuationResult(
            method="Asset-Based Valuation",
            intrinsic_value=20.00,
            current_price=17.50,
            margin_of_safety=0.125,  # 12.5% margin
            confidence="medium",
            assumptions=[
                "Using Tangible Book Value",
                "Excludes goodwill and intangibles"
            ],
            warnings=["Asset values may not reflect liquidation values"]
        ),
        ValuationResult(
            method="Conservative DCF",
            intrinsic_value=32.15,
            current_price=17.50,
            margin_of_safety=0.46,  # 46% margin
            confidence="medium",
            assumptions=[
                "Growth rate: 5.0% (capped at 5%)",
                "Terminal growth: 2.5%",
                "Discount rate: 12.0%",
                "10-year projection period"
            ],
            warnings=[]
        )
    ]
    
    # Triangulated value (weighted by confidence)
    triangulated_value = 28.85  # High confidence EPV gets more weight
    
    return ScreenResult(
        ticker="VALUE",
        company_name="Value Industries Inc",
        sector="Industrials",
        current_price=17.50,
        intrinsic_value=triangulated_value,
        margin_of_safety=(triangulated_value - 17.50) / triangulated_value,
        triangulated_value=triangulated_value,
        valuations=valuations,
        metrics=metrics,
        graham_score=87.5,  # Excellent Graham score
        rank=1
    )


def create_borderline_stock():
    """Create a stock that barely passes Graham criteria"""
    
    metrics = FinancialMetrics(
        ticker="BORDER",
        current_ratio=2.1,  # Just passes
        debt_to_equity=0.45,  # Close to limit
        pe_ratio=14.8,  # Just under 15
        pb_ratio=1.4,  # Just under 1.5
        book_value_per_share=18.00,
        earnings_per_share=1.70,
        owner_earnings=28000000,
        roe=0.12,
        earnings_growth=0.02,  # Slow growth
        dividend_years=6,
        ncav_per_share=1.20,
        tangible_book_value=16.50
    )
    
    valuations = [
        ValuationResult(
            method="Earnings Power Value (EPV)",
            intrinsic_value=26.80,
            current_price=24.20,
            margin_of_safety=0.097,  # ~10% margin
            confidence="medium",
            assumptions=[
                "10% discount rate used",
                "Owner earnings: $28,000,000"
            ],
            warnings=["Margin of safety below 30%"]
        )
    ]
    
    return ScreenResult(
        ticker="BORDER",
        company_name="Borderline Corp",
        sector="Utilities",
        current_price=24.20,
        intrinsic_value=26.80,
        margin_of_safety=0.097,
        triangulated_value=26.80,
        valuations=valuations,
        metrics=metrics,
        graham_score=62.5,  # Decent score
        rank=2
    )


async def simulate_successful_scan():
    """Simulate what happens when the screener finds qualifying stocks"""
    
    print("🎯 SIMULATION: Graham Screener Finding Value Stocks")
    print("=" * 60)
    
    # Create sample results
    value_stock = create_sample_value_stock()
    borderline_stock = create_borderline_stock()
    
    results = [value_stock, borderline_stock]
    
    # Simulate the screening output
    print(f"✅ Found {len(results)} stocks that passed Graham's criteria!")
    print(f"📊 Analyzed sample of randomly selected stocks")
    print()
    
    print("📈 TOP QUALIFYING STOCKS:")
    print("-" * 40)
    
    for stock in results:
        print(f"#{stock.rank}. {stock.ticker} - {stock.company_name}")
        print(f"   Sector: {stock.sector}")
        print(f"   Current Price: ${stock.current_price:.2f}")
        print(f"   Intrinsic Value: ${stock.intrinsic_value:.2f}")
        print(f"   Margin of Safety: {stock.margin_of_safety:.1%}")
        print(f"   Graham Score: {stock.graham_score:.1f}/100")
        print(f"   Key Strengths:")
        
        if stock.metrics.current_ratio >= 2.0:
            print(f"     ✅ Strong liquidity (Current Ratio: {stock.metrics.current_ratio:.1f})")
        if stock.metrics.debt_to_equity <= 0.5:
            print(f"     ✅ Conservative debt (D/E: {stock.metrics.debt_to_equity:.2f})")
        if stock.metrics.pe_ratio <= 15.0:
            print(f"     ✅ Reasonable valuation (P/E: {stock.metrics.pe_ratio:.1f})")
        if stock.metrics.pb_ratio <= 1.5:
            print(f"     ✅ Asset value (P/B: {stock.metrics.pb_ratio:.1f})")
        
        print()
    
    # Show what files would be generated
    print("📄 OUTPUT FILES GENERATED:")
    print("-" * 40)
    print("✅ output/top_10.csv - Summary spreadsheet")
    print("✅ output/top_10.json - Machine-readable data")
    print("✅ output/reports/VALUE.md - Detailed VALUE analysis")
    print("✅ output/reports/BORDER.md - Detailed BORDER analysis")
    print()
    
    # Generate actual sample report
    config = Config(output_dir=Path('simulation_output'))
    report_gen = ReportGenerator(config)
    
    await report_gen.generate_company_report(value_stock)
    print(f"📋 Sample report generated: simulation_output/reports/VALUE.md")
    print()
    
    print("🎉 This demonstrates what happens when the Graham screener")
    print("   finds stocks that meet Benjamin Graham's strict criteria!")
    print()
    print("💡 In practice, qualifying stocks are rare because:")
    print("   • Most stocks trade at higher valuations in today's market")
    print("   • Graham's criteria are intentionally very conservative")
    print("   • Only 1-5% of stocks typically pass all filters")
    print("   • This selectivity is exactly what Graham intended!")


if __name__ == "__main__":
    asyncio.run(simulate_successful_scan())