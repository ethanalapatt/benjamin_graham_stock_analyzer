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

