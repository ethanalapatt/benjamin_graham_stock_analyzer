"""Data provider interfaces and implementations"""

import asyncio
import logging
import ssl
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import pandas as pd
import requests
from pathlib import Path

from .config import Config
from .api_keys import alpha_vantage_key_manager


@dataclass
class FinancialStatement:
    ticker: str
    year: int
    statement_type: str  # 'income', 'balance', 'cash_flow'
    data: Dict[str, Any]
    filing_url: Optional[str] = None
    filing_date: Optional[datetime] = None


@dataclass
class CompanyProfile:
    ticker: str
    name: str
    sector: str
    industry: str
    market_cap: Optional[float] = None
    description: Optional[str] = None
    exchange: Optional[str] = None


class DataProvider(ABC):
    """Abstract base class for financial data providers"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def get_company_profile(self, ticker: str) -> Optional[CompanyProfile]:
        """Get basic company information"""
        pass
    
    @abstractmethod
    async def get_financial_statements(self, ticker: str, years: int = 7) -> List[FinancialStatement]:
        """Get financial statements for specified years"""
        pass
    
    @abstractmethod
    async def get_stock_price(self, ticker: str, date: Optional[datetime] = None) -> Optional[float]:
        """Get stock price for a specific date (current if None)"""
        pass
    
    @abstractmethod
    async def get_nyse_tickers(self) -> List[str]:
        """Get list of NYSE ticker symbols"""
        pass


class AlphaVantageProvider(DataProvider):
    """Alpha Vantage API implementation"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, config: Config):
        super().__init__(config)
        # Use provided API key or get one from the key manager
        self.api_key = config.api_key or alpha_vantage_key_manager.get_current_key() or "demo"
        self.key_manager = alpha_vantage_key_manager if not config.api_key else None
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None:
            # Create SSL context that doesn't verify certificates (for development)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session
    
    async def _make_request(self, params: Dict[str, str], retry_count: int = 0) -> Optional[Dict]:
        if self.config.dry_run:
            self.logger.info(f"DRY RUN: Would call Alpha Vantage with {params}")
            return None
            
        session = await self._get_session()
        params['apikey'] = self.api_key
        
        try:
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for rate limiting message
                    if 'Note' in data and 'call frequency' in data['Note']:
                        self.logger.warning(f"Rate limited with key ending in ...{self.api_key[-4:]}")
                        if self.key_manager and retry_count < 3:
                            self.key_manager.rotate_key()
                            self.api_key = self.key_manager.get_current_key()
                            self.logger.info(f"Rotating to key ending in ...{self.api_key[-4:]}")
                            await asyncio.sleep(1)
                            return await self._make_request(params, retry_count + 1)
                        return None
                    
                    if 'Error Message' in data:
                        self.logger.error(f"Alpha Vantage error: {data['Error Message']}")
                        return None
                    
                    self.request_count += 1
                    if self.request_count % 10 == 0:
                        self.logger.info(f"Made {self.request_count} API requests with key ...{self.api_key[-4:]}")
                    
                    return data
                else:
                    self.logger.error(f"HTTP error {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Request failed: {str(e)}")
            return None
    
    async def get_company_profile(self, ticker: str) -> Optional[CompanyProfile]:
        params = {
            'function': 'OVERVIEW',
            'symbol': ticker
        }
        
        data = await self._make_request(params)
        if not data:
            return None
            
        try:
            return CompanyProfile(
                ticker=ticker,
                name=data.get('Name', ''),
                sector=data.get('Sector', ''),
                industry=data.get('Industry', ''),
                market_cap=float(data.get('MarketCapitalization', 0)) if data.get('MarketCapitalization') else None,
                description=data.get('Description', ''),
                exchange=data.get('Exchange', '')
            )
        except (ValueError, KeyError) as e:
            self.logger.error(f"Error parsing company profile for {ticker}: {str(e)}")
            return None
    
    async def get_financial_statements(self, ticker: str, years: int = 7) -> List[FinancialStatement]:
        statements = []
        
        # Get Income Statement
        income_data = await self._get_financial_statement(ticker, 'INCOME_STATEMENT')
        if income_data:
            statements.extend(self._parse_statements(ticker, income_data, 'income', years))
        
        # Get Balance Sheet
        balance_data = await self._get_financial_statement(ticker, 'BALANCE_SHEET')
        if balance_data:
            statements.extend(self._parse_statements(ticker, balance_data, 'balance', years))
        
        # Get Cash Flow
        cash_flow_data = await self._get_financial_statement(ticker, 'CASH_FLOW')
        if cash_flow_data:
            statements.extend(self._parse_statements(ticker, cash_flow_data, 'cash_flow', years))
        
        return statements
    
    async def _get_financial_statement(self, ticker: str, function: str) -> Optional[Dict]:
        params = {
            'function': function,
            'symbol': ticker
        }
        return await self._make_request(params)
    
    def _parse_statements(self, ticker: str, data: Dict, statement_type: str, years: int) -> List[FinancialStatement]:
        statements = []
        annual_reports = data.get('annualReports', [])
        
        for i, report in enumerate(annual_reports[:years]):
            try:
                fiscal_date = datetime.strptime(report['fiscalDateEnding'], '%Y-%m-%d')
                year = fiscal_date.year
                
                statements.append(FinancialStatement(
                    ticker=ticker,
                    year=year,
                    statement_type=statement_type,
                    data=report,
                    filing_date=fiscal_date
                ))
            except (ValueError, KeyError) as e:
                self.logger.warning(f"Error parsing {statement_type} for {ticker}, report {i}: {str(e)}")
                continue
        
        return statements
    
    async def get_stock_price(self, ticker: str, date: Optional[datetime] = None) -> Optional[float]:
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': ticker
        }
        
        data = await self._make_request(params)
        if not data:
            return None
        
        try:
            quote = data.get('Global Quote', {})
            price = float(quote.get('05. price', 0))
            return price if price > 0 else None
        except (ValueError, KeyError):
            return None
    
    async def get_nyse_tickers(self) -> List[str]:
        # Alpha Vantage doesn't provide a direct ticker list endpoint
        # Fall back to hardcoded list or external source
        return await self._get_tickers_from_nasdaq_trader()
    
    async def _get_tickers_from_nasdaq_trader(self) -> List[str]:
        """Fallback method to get NYSE tickers - returns mock data in dry run"""
        if self.config.dry_run:
            # Return sample NYSE tickers for testing
            mock_tickers = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 
                'META', 'NVDA', 'JPM', 'JNJ', 'V',
                'PG', 'UNH', 'HD', 'MA', 'DIS'
            ]
            self.logger.info(f"Using mock NYSE tickers: {len(mock_tickers)} symbols")
            return mock_tickers
        
        try:
            # Try HTTPS URL instead of FTP
            url = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            lines = response.text.strip().split('\n')[1:-1]  # Skip header and footer
            
            nyse_tickers = []
            for line in lines:
                parts = line.split('|')
                if len(parts) >= 3 and 'N' in parts[2]:  # NYSE exchange
                    ticker = parts[0].strip()
                    if ticker and not any(c in ticker for c in ['.', '^', '$']):
                        nyse_tickers.append(ticker)
            
            self.logger.info(f"Found {len(nyse_tickers)} NYSE tickers")
            return nyse_tickers
            
        except Exception as e:
            self.logger.warning(f"Error fetching NYSE tickers: {str(e)}")
            # Fallback to mock data
            mock_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
            self.logger.info(f"Using fallback tickers: {len(mock_tickers)} symbols")
            return mock_tickers
    
    async def close(self):
        if self.session:
            await self.session.close()


class FinancialModelingPrepProvider(DataProvider):
    """Financial Modeling Prep API implementation"""
    
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.api_key = config.api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_company_profile(self, ticker: str) -> Optional[CompanyProfile]:
        # Implementation similar to AlphaVantage but with FMP endpoints
        if self.config.dry_run:
            return CompanyProfile(ticker=ticker, name=f"Mock {ticker}", sector="Technology", industry="Software")
        # TODO: Implement FMP-specific API calls
        return None
    
    async def get_financial_statements(self, ticker: str, years: int = 7) -> List[FinancialStatement]:
        # TODO: Implement FMP-specific financial statements
        return []
    
    async def get_stock_price(self, ticker: str, date: Optional[datetime] = None) -> Optional[float]:
        # TODO: Implement FMP-specific price fetching
        return None
    
    async def get_nyse_tickers(self) -> List[str]:
        # TODO: Implement FMP-specific ticker list
        return []


class DataProviderFactory:
    """Factory for creating data provider instances"""
    
    @staticmethod
    def create(config: Config) -> DataProvider:
        if config.data_provider == 'alpha_vantage':
            return AlphaVantageProvider(config)
        elif config.data_provider == 'fmp':
            return FinancialModelingPrepProvider(config)
        elif config.data_provider == 'tiingo':
            # TODO: Implement Tiingo provider
            raise NotImplementedError("Tiingo provider not yet implemented")
        elif config.data_provider == 'polygon':
            # TODO: Implement Polygon provider
            raise NotImplementedError("Polygon provider not yet implemented")
        else:
            raise ValueError(f"Unknown data provider: {config.data_provider}")