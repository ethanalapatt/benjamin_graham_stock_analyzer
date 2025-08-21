"""Report generation for Graham screener results"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
import asyncio

if TYPE_CHECKING:
    from .screener import ScreenResult
    from .config import Config


class ReportGenerator:
    """Generate detailed company reports in markdown format"""
    
    def __init__(self, config: 'Config'):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Create reports directory
        self.reports_dir = self.config.output_dir / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
    
    async def generate_company_report(self, result: 'ScreenResult'):
        """Generate detailed markdown report for a company"""
        
        report_path = self.reports_dir / f"{result.ticker}.md"
        
        content = self._build_report_content(result)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"Company report generated: {report_path}")
    
    def _build_report_content(self, result: 'ScreenResult') -> str:
        """Build the markdown content for a company report"""
        
        report = []
        
        # Header
        report.append(f"# {result.company_name} ({result.ticker})")
        report.append(f"**Benjamin Graham Value Analysis Report**")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Executive Summary
        report.extend(self._build_executive_summary(result))
        
        # Key Metrics Table
        report.extend(self._build_key_metrics_table(result))
        
        # Valuation Analysis
        report.extend(self._build_valuation_analysis(result))
        
        # Graham Score Breakdown
        report.extend(self._build_graham_score_breakdown(result))
        
        # Conservative Adjustments
        report.extend(self._build_adjustments_section(result))
        
        # Risk Factors
        report.extend(self._build_risk_factors(result))
        
        # Data Sources and Assumptions
        report.extend(self._build_assumptions_section(result))
        
        # JSON Data Block
        report.extend(self._build_json_block(result))
        
        return "\n".join(report)
    
    def _build_executive_summary(self, result: 'ScreenResult') -> list:
        """Build executive summary section"""
        
        summary = [
            "## Executive Summary",
            "",
            f"**Sector:** {result.sector}",
            f"**Current Price:** ${result.current_price:.2f}",
            f"**Intrinsic Value:** ${result.intrinsic_value:.2f}",
            f"**Margin of Safety:** {result.margin_of_safety:.1%}",
            f"**Graham Score:** {result.graham_score:.1f}/100",
            f"**Rank:** #{result.rank}",
            ""
        ]
        
        # Investment thesis
        if result.margin_of_safety >= 0.5:
            thesis = "**Strong Value Opportunity** - Meets Benjamin Graham's conservative criteria with substantial margin of safety."
        elif result.margin_of_safety >= 0.3:
            thesis = "**Moderate Value Opportunity** - Decent margin of safety but requires careful analysis."
        else:
            thesis = "**Speculative** - Limited margin of safety, high risk relative to Graham's principles."
        
        summary.append(f"**Investment Thesis:** {thesis}")
        summary.append("")
        
        return summary
    
    def _build_key_metrics_table(self, result: 'ScreenResult') -> list:
        """Build key financial metrics table"""
        
        metrics = result.metrics
        
        table = [
            "## Key Financial Metrics",
            "",
            "| Metric | Value | Graham Criterion | Status |",
            "|--------|-------|------------------|--------|"
        ]
        
        # Current Ratio
        cr_status = "✅ Pass" if metrics.current_ratio and metrics.current_ratio >= 2.0 else "❌ Fail"
        cr_value = f"{metrics.current_ratio:.2f}" if metrics.current_ratio else "N/A"
        table.append(f"| Current Ratio | {cr_value} | ≥ 2.0 | {cr_status} |")
        
        # Debt to Equity
        de_status = "✅ Pass" if metrics.debt_to_equity is not None and metrics.debt_to_equity <= 0.5 else "❌ Fail"
        de_value = f"{metrics.debt_to_equity:.2f}" if metrics.debt_to_equity is not None else "N/A"
        table.append(f"| Debt/Equity | {de_value} | ≤ 0.5 | {de_status} |")
        
        # PE Ratio
        pe_status = "✅ Pass" if metrics.pe_ratio and metrics.pe_ratio <= 15.0 else "❌ Fail"
        pe_value = f"{metrics.pe_ratio:.2f}" if metrics.pe_ratio else "N/A"
        table.append(f"| P/E Ratio | {pe_value} | ≤ 15.0 | {pe_status} |")
        
        # PB Ratio
        pb_status = "✅ Pass" if metrics.pb_ratio and metrics.pb_ratio <= 1.5 else "❌ Fail"
        pb_value = f"{metrics.pb_ratio:.2f}" if metrics.pb_ratio else "N/A"
        table.append(f"| P/B Ratio | {pb_value} | ≤ 1.5 | {pb_status} |")
        
        # PE × PB
        if metrics.pe_ratio and metrics.pb_ratio:
            pe_pb = metrics.pe_ratio * metrics.pb_ratio
            pe_pb_status = "✅ Pass" if pe_pb <= 22.5 else "❌ Fail"
            table.append(f"| P/E × P/B | {pe_pb:.1f} | ≤ 22.5 | {pe_pb_status} |")
        
        # ROE
        roe_value = f"{metrics.roe:.1%}" if metrics.roe else "N/A"
        table.append(f"| Return on Equity | {roe_value} | > 0% | {roe_value} |")
        
        # Earnings Growth
        eg_value = f"{metrics.earnings_growth:.1%}" if metrics.earnings_growth else "N/A"
        table.append(f"| Earnings Growth | {eg_value} | Consistent | {eg_value} |")
        
        # Book Value per Share
        bv_value = f"${metrics.book_value_per_share:.2f}" if metrics.book_value_per_share else "N/A"
        table.append(f"| Book Value/Share | {bv_value} | > $0 | {bv_value} |")
        
        table.append("")
        return table
    
    def _build_valuation_analysis(self, result: 'ScreenResult') -> list:
        """Build detailed valuation analysis"""
        
        analysis = [
            "## Valuation Analysis",
            "",
            f"**Triangulated Intrinsic Value:** ${result.intrinsic_value:.2f}",
            f"**Current Market Price:** ${result.current_price:.2f}",
            f"**Margin of Safety:** {result.margin_of_safety:.1%}",
            ""
        ]
        
        for i, valuation in enumerate(result.valuations, 1):
            analysis.extend([
                f"### {i}. {valuation.method}",
                "",
                f"**Intrinsic Value:** ${valuation.intrinsic_value:.2f}",
                f"**Margin of Safety:** {valuation.margin_of_safety:.1%}",
                f"**Confidence Level:** {valuation.confidence.title()}",
                ""
            ])
            
            if valuation.assumptions:
                analysis.append("**Key Assumptions:**")
                for assumption in valuation.assumptions:
                    analysis.append(f"- {assumption}")
                analysis.append("")
            
            if valuation.warnings:
                analysis.append("**Warnings:**")
                for warning in valuation.warnings:
                    analysis.append(f"- ⚠️ {warning}")
                analysis.append("")
        
        return analysis
    
    def _build_graham_score_breakdown(self, result: 'ScreenResult') -> list:
        """Build Graham score breakdown"""
        
        breakdown = [
            "## Graham Score Breakdown",
            "",
            f"**Total Score:** {result.graham_score:.1f}/100",
            "",
            "The Graham Score evaluates stocks across multiple dimensions of Benjamin Graham's investment philosophy:",
            "",
            "- **Liquidity (0-20 pts):** Current ratio strength",
            "- **Leverage (0-15 pts):** Debt management",
            "- **Valuation (0-25 pts):** P/E and P/B ratios",
            "- **Growth (0-15 pts):** Earnings consistency",
            "- **Dividends (0-10 pts):** Dividend track record",
            "- **Safety Margin (0-15 pts):** Margin of safety bonus",
            ""
        ]
        
        # Score interpretation
        if result.graham_score >= 80:
            interpretation = "**Excellent** - Outstanding candidate meeting most of Graham's strict criteria"
        elif result.graham_score >= 60:
            interpretation = "**Good** - Solid value stock with minor concerns"
        elif result.graham_score >= 40:
            interpretation = "**Fair** - Some value characteristics but significant risks"
        else:
            interpretation = "**Poor** - Does not meet Graham's conservative standards"
        
        breakdown.append(f"**Score Interpretation:** {interpretation}")
        breakdown.append("")
        
        return breakdown
    
    def _build_adjustments_section(self, result: 'ScreenResult') -> list:
        """Build conservative adjustments section"""
        
        adjustments = [
            "## Conservative Adjustments Applied",
            "",
            "This analysis applies Benjamin Graham's conservative approach with the following adjustments:",
            "",
            f"- **Capital Expenditures:** Increased by {(self.config.capex_multiplier - 1) * 100:.0f}% for maintenance estimates",
            f"- **Depreciation:** Conservative factor of {self.config.depreciation_conservatism:.1f}x applied",
            f"- **Working Capital:** Haircut of {(1 - self.config.working_capital_adjustment) * 100:.0f}% applied",
            "- **Intangible Assets:** Excluded from tangible book value calculations",
            "- **Growth Assumptions:** Capped at 5% annually in DCF analysis",
            "- **Discount Rates:** 10-12% used (higher than current risk-free rates)",
            ""
        ]
        
        return adjustments
    
    def _build_risk_factors(self, result: 'ScreenResult') -> list:
        """Build risk factors section"""
        
        risks = [
            "## Risk Factors & Considerations",
            ""
        ]
        
        # Collect all warnings from valuations
        all_warnings = []
        for valuation in result.valuations:
            all_warnings.extend(valuation.warnings)
        
        if all_warnings:
            risks.append("**Valuation Risks:**")
            for warning in set(all_warnings):  # Remove duplicates
                risks.append(f"- {warning}")
            risks.append("")
        
        # General Graham investment risks
        risks.extend([
            "**General Investment Risks:**",
            "- Value traps: Stock may be cheap for fundamental reasons",
            "- Market conditions: Value investing can underperform in growth markets",
            "- Management quality: Not directly assessed in quantitative screening",
            "- Industry disruption: Financial metrics may not capture technological obsolescence",
            "- Liquidity: Some value stocks may have limited trading volume",
            ""
        ])
        
        return risks
    
    def _build_assumptions_section(self, result: 'ScreenResult') -> list:
        """Build assumptions and data sources section"""
        
        assumptions = [
            "## Assumptions & Data Sources",
            "",
            "**Key Assumptions:**",
            "- Financial data accuracy depends on company filings",
            "- Market prices reflect current sentiment, not intrinsic value",
            "- Historical performance patterns may continue",
            "- Conservative estimates favor safety over precision",
            "",
            "**Data Sources:**",
            f"- Financial data: {self.config.data_provider.title()}",
            "- SEC filings: Referenced for audit trail",
            "- Market prices: Real-time or latest available",
            "",
            "**Analysis Date:** " + datetime.now().strftime('%Y-%m-%d'),
            "",
            "**Disclaimer:** This analysis is for educational purposes only and should not be considered as investment advice. Always conduct your own research and consult with financial professionals before making investment decisions.",
            ""
        ]
        
        return assumptions
    
    def _build_json_block(self, result: 'ScreenResult') -> list:
        """Build machine-readable JSON data block"""
        
        json_block = [
            "## Machine-Readable Data",
            "",
            "```json",
            json.dumps(result.to_dict(), indent=2, default=str),
            "```",
            ""
        ]
        
        return json_block