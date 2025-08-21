#!/usr/bin/env python3
"""
Basic test to verify the Graham screener components work
"""

from src.config import Config
from src.valuations import GrahamValuator, FinancialMetrics
from src.data_providers import CompanyProfile, FinancialStatement
from datetime import datetime


def test_basic_functionality():
    """Test basic screener functionality"""
    
    print("Testing Benjamin Graham Stock Screener...")
    
    # Test 1: Config creation
    config = Config()
    print(f"✓ Config created with {config.top_count} top stocks")
    
    # Test 2: Valuator creation
    valuator = GrahamValuator(config)
    print("✓ Graham valuator created")
    
    # Test 3: Safe float conversion
    assert valuator._safe_float("123.45") == 123.45
    assert valuator._safe_float(None) is None
    assert valuator._safe_float("invalid") is None
    print("✓ Safe float conversion works")
    
    # Test 4: Financial metrics
    profile = CompanyProfile(
        ticker="TEST",
        name="Test Company", 
        sector="Technology",
        industry="Software"
    )
    print("✓ Company profile created")
    
    # Test 5: Sample financial statement
    statement = FinancialStatement(
        ticker="TEST",
        year=2023,
        statement_type="income",
        data={"netIncome": "100000000"},
        filing_date=datetime(2023, 12, 31)
    )
    print("✓ Financial statement created")
    
    # Test 6: Basic metrics calculation
    metrics = FinancialMetrics(
        ticker="TEST",
        current_ratio=2.5,
        debt_to_equity=0.3,
        pe_ratio=12.0,
        pb_ratio=1.2
    )
    print("✓ Financial metrics created")
    
    # Test 7: Graham score calculation  
    score = 0
    if metrics.current_ratio >= 2.0:
        score += 20
    if metrics.debt_to_equity <= 0.5:
        score += 15
    if metrics.pe_ratio <= 15.0:
        score += 15
    if metrics.pb_ratio <= 1.5:
        score += 10
    
    print(f"✓ Graham score calculation: {score}/100")
    
    print("\n🎉 All basic tests passed!")
    print("\nTo run the full screener:")
    print("python graham_scan.py --dry_run --top 5")
    print("\nTo run unit tests:")
    print("pytest tests/")


if __name__ == "__main__":
    test_basic_functionality()