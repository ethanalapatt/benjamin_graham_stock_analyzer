"""SEC EDGAR filing integration for audit trails"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import aiohttp
import json
from urllib.parse import urljoin

from .config import Config


class SECFilingProvider:
    """Fetch SEC filing URLs and metadata for audit trails"""
    
    EDGAR_BASE_URL = "https://www.sec.gov/Archives/"
    COMPANY_SEARCH_URL = "https://www.sec.gov/files/company_tickers.json"
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # SEC requires user agent identification
        self.headers = {
            'User-Agent': 'Graham Stock Screener 1.0 (contact@example.com)',
            'Accept': 'application/json'
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with SEC-compliant headers"""
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
    
    async def get_filing_urls(self, ticker: str, years: int = 7) -> List[Dict]:
        """Get SEC filing URLs for a company"""
        
        if self.config.dry_run:
            return self._mock_filing_urls(ticker, years)
        
        try:
            # Get CIK for the ticker
            cik = await self._get_cik_for_ticker(ticker)
            if not cik:
                self.logger.warning(f"Could not find CIK for ticker {ticker}")
                return []
            
            # Get recent filings
            filings = await self._get_company_filings(cik, years)
            return filings
            
        except Exception as e:
            self.logger.error(f"Error fetching SEC filings for {ticker}: {str(e)}")
            return []
    
    async def _get_cik_for_ticker(self, ticker: str) -> Optional[str]:
        """Get CIK (Central Index Key) for a ticker symbol"""
        
        session = await self._get_session()
        
        try:
            async with session.get(self.COMPANY_SEARCH_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Search for ticker in the company tickers mapping
                    for cik, company_info in data.items():
                        if isinstance(company_info, dict):
                            company_ticker = company_info.get('ticker', '').upper()
                            if company_ticker == ticker.upper():
                                return str(cik).zfill(10)  # Pad CIK to 10 digits
                    
                    self.logger.debug(f"Ticker {ticker} not found in SEC company tickers")
                    return None
                else:
                    self.logger.error(f"SEC API error: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error fetching CIK for {ticker}: {str(e)}")
            return None
    
    async def _get_company_filings(self, cik: str, years: int) -> List[Dict]:
        """Get recent filings for a company by CIK"""
        
        session = await self._get_session()
        
        # SEC EDGAR company filings URL
        filings_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        
        try:
            async with session.get(filings_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_filing_data(data, years)
                elif response.status == 429:
                    # Rate limited - wait and retry once
                    self.logger.warning("SEC rate limit hit, waiting...")
                    await asyncio.sleep(10)
                    async with session.get(filings_url) as retry_response:
                        if retry_response.status == 200:
                            data = await retry_response.json()
                            return self._parse_filing_data(data, years)
                
                self.logger.error(f"SEC filings API error: {response.status}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching filings for CIK {cik}: {str(e)}")
            return []
    
    def _parse_filing_data(self, data: Dict, years: int) -> List[Dict]:
        """Parse SEC filing data and extract relevant 10-K and 10-Q filings"""
        
        filings = []
        cutoff_date = datetime.now() - timedelta(days=years * 365)
        
        recent_filings = data.get('filings', {}).get('recent', {})
        
        if not recent_filings:
            return []
        
        # Get arrays of filing data
        forms = recent_filings.get('form', [])
        filing_dates = recent_filings.get('filingDate', [])
        accession_numbers = recent_filings.get('accessionNumber', [])
        primary_documents = recent_filings.get('primaryDocument', [])
        
        for i in range(len(forms)):
            try:
                form = forms[i]
                filing_date_str = filing_dates[i]
                accession_number = accession_numbers[i]
                primary_doc = primary_documents[i]
                
                # Only interested in annual (10-K) and quarterly (10-Q) reports
                if form not in ['10-K', '10-Q', '10-K/A', '10-Q/A']:
                    continue
                
                # Parse filing date
                filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d')
                
                # Skip if too old
                if filing_date < cutoff_date:
                    continue
                
                # Build filing URL
                accession_clean = accession_number.replace('-', '')
                filing_url = f"{self.EDGAR_BASE_URL}edgar/data/{data.get('cik', '')}/{accession_clean}/{primary_doc}"
                
                filings.append({
                    'form_type': form,
                    'filing_date': filing_date.isoformat(),
                    'accession_number': accession_number,
                    'filing_url': filing_url,
                    'year': filing_date.year,
                    'quarter': self._get_quarter(filing_date)
                })
                
            except (IndexError, ValueError, KeyError) as e:
                self.logger.debug(f"Error parsing filing {i}: {str(e)}")
                continue
        
        # Sort by filing date (newest first)
        filings.sort(key=lambda x: x['filing_date'], reverse=True)
        
        return filings
    
    def _get_quarter(self, date: datetime) -> int:
        """Get quarter number from date"""
        return (date.month - 1) // 3 + 1
    
    def _mock_filing_urls(self, ticker: str, years: int) -> List[Dict]:
        """Generate mock filing URLs for dry run mode"""
        
        filings = []
        current_year = datetime.now().year
        
        for year in range(current_year - years + 1, current_year + 1):
            # Annual 10-K
            filings.append({
                'form_type': '10-K',
                'filing_date': f"{year}-03-15",
                'accession_number': f"0000000000-{year}-000001",
                'filing_url': f"https://www.sec.gov/Archives/edgar/data/mock/{ticker}-10K-{year}.htm",
                'year': year,
                'quarter': 1
            })
            
            # Quarterly 10-Qs
            for quarter in [1, 2, 3]:
                month = quarter * 3 + 2  # May, Aug, Nov
                filings.append({
                    'form_type': '10-Q',
                    'filing_date': f"{year}-{month:02d}-15",
                    'accession_number': f"0000000000-{year}-00000{quarter + 1}",
                    'filing_url': f"https://www.sec.gov/Archives/edgar/data/mock/{ticker}-10Q-{year}Q{quarter}.htm",
                    'year': year,
                    'quarter': quarter
                })
        
        return filings
    
    def get_filing_for_year(self, filings: List[Dict], year: int, form_type: str = '10-K') -> Optional[Dict]:
        """Get specific filing for a year"""
        
        for filing in filings:
            if filing['year'] == year and filing['form_type'] == form_type:
                return filing
        
        return None
    
    def build_audit_trail(self, ticker: str, filings: List[Dict], adjustments: List[str]) -> Dict:
        """Build audit trail linking data points to SEC filings"""
        
        audit_trail = {
            'ticker': ticker,
            'analysis_date': datetime.now().isoformat(),
            'data_sources': {
                'sec_filings': filings,
                'adjustments_applied': adjustments
            },
            'methodology': {
                'valuation_methods': ['Earnings Power Value', 'Asset-Based', 'Conservative DCF'],
                'conservative_assumptions': [
                    'No growth in EPV calculation',
                    '20% haircut on tangible assets',
                    'Capped growth rates at 5% in DCF',
                    'Elevated discount rates (10-12%)'
                ],
                'graham_criteria': [
                    'Current ratio >= 2.0',
                    'Debt/equity <= 0.5',
                    'PE <= 15.0',
                    'PB <= 1.5',
                    'PE × PB <= 22.5',
                    'Consistent positive earnings',
                    'Margin of safety >= 50%'
                ]
            }
        }
        
        return audit_trail
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()