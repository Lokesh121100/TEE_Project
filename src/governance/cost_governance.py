# 💰 ARIA Governance - Cost Governance & ROI Dashboard
# Track costs, ROI, and cost optimization

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json

@dataclass
class CostBreakdown:
    """Cost breakdown for a period"""
    period: str
    total_cost: float
    fixed_costs: float
    variable_costs: float
    tickets_processed: int
    cost_per_ticket: float
    roi_value: float
    roi_percentage: float

class CostGovernanceService:
    """Service for tracking and optimizing ARIA costs and ROI"""

    # Fixed monthly costs (in USD)
    FIXED_COSTS = {
        'ollama_server': 2000,           # GPU server
        'azure_infrastructure': 500,      # Hosting, storage
        'azure_database': 300,           # SQL Database
        'servicenow_licensing': 1500,    # ServiceNow license
    }

    # Variable costs per 1000 tickets (in USD)
    VARIABLE_COSTS = {
        'llm_inference': 10,             # LLM inference cost
        'storage': 5,                    # Data storage
        'operations_support': 25,        # Support & operations
    }

    # Value per ticket by resolution type (in USD)
    TICKET_VALUES = {
        'auto_resolved': 75,             # Full automation
        'ai_assisted': 45,               # Assisted with human verification
        'escalated': 20,                 # Standard escalation handling
    }

    def __init__(self, db_path: str = "data/aria_governance.db"):
        self.db_path = db_path
        self.monthly_fixed_cost = sum(self.FIXED_COSTS.values())

    def record_cost(self, category: str, amount: float, description: str,
                   ticket_count: int = 0) -> str:
        """Record a cost entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cost_id = f"COST-{datetime.now().isoformat()}"

        try:
            cost_per_ticket = (amount / ticket_count) if ticket_count > 0 else 0

            cursor.execute("""
                INSERT INTO aria_cost_tracking
                (cost_id, date_utc, category, amount, description, ticket_count, cost_per_ticket)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (cost_id, datetime.utcnow().isoformat(), category, amount, description, ticket_count, cost_per_ticket))

            conn.commit()
            return cost_id
        finally:
            conn.close()

    def get_monthly_cost_breakdown(self, year: int, month: int) -> CostBreakdown:
        """Calculate monthly cost breakdown"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get variable costs from actual tracking
        month_str = f"{year}-{month:02d}"
        cursor.execute("""
            SELECT SUM(amount) as total_variable
            FROM aria_cost_tracking
            WHERE date_utc LIKE ?
        """, (f"{month_str}%",))

        cost_result = cursor.fetchone()
        variable_cost = cost_result['total_variable'] or 0

        # Get ticket metrics
        cursor.execute("""
            SELECT
                COUNT(*) as total_tickets,
                SUM(CASE WHEN was_auto_resolved = 1 THEN 1 ELSE 0 END) as auto_resolved,
                SUM(CASE WHEN was_escalated = 1 AND was_auto_resolved = 0 THEN 1 ELSE 0 END) as escalated,
                SUM(CASE WHEN was_auto_resolved = 0 AND was_escalated = 0 THEN 1 ELSE 0 END) as ai_assisted
            FROM aria_audit_log
            WHERE strftime('%Y-%m', timestamp_utc) = ?
        """, (month_str,))

        ticket_result = cursor.fetchone()
        conn.close()

        # Calculate metrics
        total_tickets = ticket_result['total_tickets'] or 0
        auto_resolved = ticket_result['auto_resolved'] or 0
        escalated = ticket_result['escalated'] or 0
        ai_assisted = ticket_result['ai_assisted'] or 0

        total_cost = self.monthly_fixed_cost + variable_cost
        cost_per_ticket = (total_cost / total_tickets) if total_tickets > 0 else 0

        # Calculate ROI value
        roi_value = (
            auto_resolved * self.TICKET_VALUES['auto_resolved'] +
            ai_assisted * self.TICKET_VALUES['ai_assisted'] +
            escalated * self.TICKET_VALUES['escalated']
        )

        roi_percentage = ((roi_value - total_cost) / roi_value * 100) if roi_value > 0 else 0

        return CostBreakdown(
            period=month_str,
            total_cost=total_cost,
            fixed_costs=self.monthly_fixed_cost,
            variable_costs=variable_cost,
            tickets_processed=total_tickets,
            cost_per_ticket=cost_per_ticket,
            roi_value=roi_value,
            roi_percentage=roi_percentage
        )

    def generate_quarterly_cost_report(self, year: int, quarter: int) -> Dict[str, Any]:
        """Generate comprehensive quarterly cost report"""

        start_month = (quarter - 1) * 3 + 1
        months = list(range(start_month, start_month + 3))

        monthly_breakdowns = []
        for month in months:
            breakdown = self.get_monthly_cost_breakdown(year, month)
            monthly_breakdowns.append(breakdown)

        # Aggregate quarterly metrics
        total_cost = sum(b.total_cost for b in monthly_breakdowns)
        total_tickets = sum(b.tickets_processed for b in monthly_breakdowns)
        avg_cost_per_ticket = (total_cost / total_tickets) if total_tickets > 0 else 0
        total_roi_value = sum(b.roi_value for b in monthly_breakdowns)
        avg_roi = ((total_roi_value - total_cost) / total_roi_value * 100) if total_roi_value > 0 else 0

        # Cost driver analysis
        cost_drivers = {
            'ollama_inference': (self.FIXED_COSTS['ollama_server'] * 3 / total_cost * 100) if total_cost > 0 else 0,
            'azure_infrastructure': (self.FIXED_COSTS['azure_infrastructure'] * 3 / total_cost * 100) if total_cost > 0 else 0,
            'servicenow_licensing': (self.FIXED_COSTS['servicenow_licensing'] * 3 / total_cost * 100) if total_cost > 0 else 0,
            'operations_support': ((self.VARIABLE_COSTS['operations_support'] * total_tickets / 1000) / total_cost * 100) if total_cost > 0 else 0,
        }

        # Optimization opportunities
        optimizations = self._identify_optimizations(cost_drivers, total_cost, monthly_breakdowns)

        return {
            "report_date": datetime.now().isoformat(),
            "quarter": f"{year}-Q{quarter}",
            "financial_summary": {
                "total_spend": round(total_cost, 2),
                "tickets_processed": total_tickets,
                "cost_per_ticket": round(avg_cost_per_ticket, 2),
                "roi_value": round(total_roi_value, 2),
                "net_benefit": round(total_roi_value - total_cost, 2),
                "roi_percentage": round(avg_roi, 1),
            },
            "monthly_breakdown": [
                {
                    "month": b.period,
                    "total_cost": round(b.total_cost, 2),
                    "fixed_costs": round(b.fixed_costs, 2),
                    "variable_costs": round(b.variable_costs, 2),
                    "tickets": b.tickets_processed,
                    "cost_per_ticket": round(b.cost_per_ticket, 2),
                    "roi_value": round(b.roi_value, 2),
                    "roi_percentage": round(b.roi_percentage, 1),
                }
                for b in monthly_breakdowns
            ],
            "cost_drivers": {k: round(v, 1) for k, v in cost_drivers.items()},
            "optimization_opportunities": optimizations,
            "trend_analysis": self._analyze_cost_trends(monthly_breakdowns),
            "approved_actions": [
                "[ ] Evaluate model quantization: Estimated -30% inference cost",
                "[ ] Renew Azure commitment: Estimated -15% infrastructure cost",
                "[ ] Optimize database indexing: Estimated -20% storage cost",
            ]
        }

    def _identify_optimizations(self, cost_drivers: Dict[str, float],
                               total_cost: float,
                               monthly_data: List[CostBreakdown]) -> List[Dict[str, Any]]:
        """Identify cost optimization opportunities"""
        optimizations = []

        # Inference cost optimization
        if cost_drivers.get('ollama_inference', 0) > 40:
            optimizations.append({
                "opportunity": "Model Quantization",
                "current_impact": f"{cost_drivers['ollama_inference']:.1f}% of total cost",
                "potential_savings": "30-40%",
                "implementation": "Quantize Llama3 70B to INT8 or INT4",
                "timeline": "2-3 weeks",
                "effort": "Medium"
            })

        # Infrastructure optimization
        if cost_drivers.get('azure_infrastructure', 0) > 10:
            optimizations.append({
                "opportunity": "Azure Commitment Discount",
                "current_impact": f"{cost_drivers['azure_infrastructure']:.1f}% of total cost",
                "potential_savings": "15-25%",
                "implementation": "Purchase 1-year or 3-year Azure commitment plan",
                "timeline": "1 week",
                "effort": "Low"
            })

        # Licensing optimization
        if cost_drivers.get('servicenow_licensing', 0) > 30:
            optimizations.append({
                "opportunity": "ServiceNow License Consolidation",
                "current_impact": f"{cost_drivers['servicenow_licensing']:.1f}% of total cost",
                "potential_savings": "10-20%",
                "implementation": "Consolidate licenses, negotiate volume discount",
                "timeline": "1-2 weeks",
                "effort": "Low"
            })

        # Storage optimization
        optimizations.append({
            "opportunity": "Database Optimization",
            "current_impact": "Data storage costs",
            "potential_savings": "15-25%",
            "implementation": "Archive old audit logs, optimize indexes",
            "timeline": "1 week",
            "effort": "Low"
        })

        return optimizations

    def _analyze_cost_trends(self, monthly_data: List[CostBreakdown]) -> Dict[str, Any]:
        """Analyze cost trends over time"""
        if not monthly_data:
            return {}

        costs = [b.total_cost for b in monthly_data]
        cost_per_tickets = [b.cost_per_ticket for b in monthly_data]
        rois = [b.roi_percentage for b in monthly_data]

        # Calculate trends
        cost_trend = ((costs[-1] - costs[0]) / costs[0] * 100) if costs[0] > 0 else 0
        efficiency_trend = ((cost_per_tickets[-1] - cost_per_tickets[0]) / cost_per_tickets[0] * 100) if cost_per_tickets[0] > 0 else 0

        return {
            "total_cost_trend": f"{cost_trend:+.1f}%" if cost_trend != 0 else "Stable",
            "cost_per_ticket_trend": f"{efficiency_trend:+.1f}%" if efficiency_trend != 0 else "Stable",
            "average_roi": f"{sum(rois) / len(rois):.1f}%",
            "trend_direction": "📈 Improving" if efficiency_trend < 0 else "📉 Declining" if efficiency_trend > 0 else "→ Stable",
            "forecast_note": "Cost per ticket trending lower = Automation improving efficiency"
        }

    def forecast_annual_roi(self, current_month: int, current_year: int) -> Dict[str, Any]:
        """Forecast annual ROI based on current trends"""

        # Get year-to-date data
        ytd_cost = 0
        ytd_roi_value = 0

        for month in range(1, current_month + 1):
            breakdown = self.get_monthly_cost_breakdown(current_year, month)
            ytd_cost += breakdown.total_cost
            ytd_roi_value += breakdown.roi_value

        # Project for full year
        months_elapsed = current_month
        months_remaining = 12 - months_elapsed

        avg_monthly_cost = ytd_cost / months_elapsed if months_elapsed > 0 else self.monthly_fixed_cost
        avg_monthly_roi = ytd_roi_value / months_elapsed if months_elapsed > 0 else 0

        projected_annual_cost = ytd_cost + (avg_monthly_cost * months_remaining)
        projected_annual_roi_value = ytd_roi_value + (avg_monthly_roi * months_remaining)
        projected_net_benefit = projected_annual_roi_value - projected_annual_cost
        projected_roi_percentage = ((projected_net_benefit / projected_annual_roi_value) * 100) if projected_annual_roi_value > 0 else 0

        return {
            "year": current_year,
            "ytd_cost": round(ytd_cost, 2),
            "ytd_roi_value": round(ytd_roi_value, 2),
            "projected_annual_cost": round(projected_annual_cost, 2),
            "projected_annual_roi_value": round(projected_annual_roi_value, 2),
            "projected_net_benefit": round(projected_net_benefit, 2),
            "projected_roi_percentage": round(projected_roi_percentage, 1),
            "months_remaining": months_remaining,
            "avg_monthly_cost": round(avg_monthly_cost, 2),
            "avg_monthly_roi_value": round(avg_monthly_roi, 2),
        }

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    cost_service = CostGovernanceService()

    # Generate quarterly cost report
    report = cost_service.generate_quarterly_cost_report(2026, 1)
    print(f"\n💰 Q1 2026 COST REPORT:\n{json.dumps(report, indent=2)}")

    # Forecast annual ROI
    forecast = cost_service.forecast_annual_roi(3, 2026)
    print(f"\n📊 2026 ANNUAL ROI FORECAST:\n{json.dumps(forecast, indent=2)}")

