"""Configuration management for Graham screener"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    universe: str = 'nyse'
    tickers_csv: Optional[str] = None
    top_count: int = 10
    years: int = 7
    min_market_cap: Optional[float] = None
    data_provider: str = 'alpha_vantage'
    api_key: Optional[str] = None
    output_dir: Path = Path('output')
    dry_run: bool = False
    random_sample: Optional[int] = None
    
    # Graham screening criteria
    min_current_ratio: float = 2.0
    max_debt_to_equity: float = 0.5
    min_earnings_growth_years: int = 5
    min_dividend_years: int = 10
    max_pe_ratio: float = 15.0
    max_pb_ratio: float = 1.5
    min_margin_of_safety: float = 0.5  # 50% margin of safety required
    
    # Conservative adjustments
    capex_multiplier: float = 1.2  # Haircut capex estimates by 20%
    depreciation_conservatism: float = 1.1  # Add 10% to depreciation
    working_capital_adjustment: float = 0.9  # Haircut working capital by 10%
    
    def __post_init__(self):
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        reports_dir = self.output_dir / 'reports'
        reports_dir.mkdir(exist_ok=True)