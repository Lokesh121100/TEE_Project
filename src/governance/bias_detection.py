# 🎯 ARIA Governance - Bias Detection & Fairness Monitoring
# Automated fairness audits and bias detection

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json

@dataclass
class FairnessMetric:
    """Fairness metric result"""
    metric_name: str
    segment: str
    value: float
    target_value: float
    status: str  # PASS / WARNING / FAIL
    variance_percentage: float

class BiasDetectionService:
    """Service for detecting and monitoring AI bias in ARIA decisions"""

    def __init__(self, db_path: str = "data/aria_governance.db"):
        self.db_path = db_path
        self.fairness_thresholds = {
            "demographic_parity": 0.10,  # ±10%
            "equalized_odds": 0.10,      # ±10%
            "predictive_parity": 0.10,   # ±10%
            "calibration": 0.05,         # ±5%
            "disparate_impact": 0.20     # <20%
        }

    def get_segment_metrics(self, segment_key: str, segment_value: str,
                           start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get accuracy metrics for a specific segment

        segment_key: 'department', 'category', 'severity', 'user_type'
        segment_value: specific value to filter by
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build dynamic query based on segment
        segment_column_map = {
            'department': 'user_department',
            'category': 'incident_category',
            'severity': 'severity_level',
            'user_type': 'user_department'
        }

        segment_column = segment_column_map.get(segment_key, segment_key)

        query = f"""
        SELECT
            COUNT(*) as total_decisions,
            SUM(CASE WHEN was_aria_correct = 1 THEN 1 ELSE 0 END) as correct_decisions,
            AVG(confidence_score) as avg_confidence,
            SUM(CASE WHEN was_escalated = 1 THEN 1 ELSE 0 END) as escalated_count,
            SUM(CASE WHEN was_overridden = 1 THEN 1 ELSE 0 END) as override_count
        FROM aria_audit_log
        WHERE {segment_column} = ?
        AND timestamp_utc BETWEEN ? AND ?
        """

        cursor.execute(query, (segment_value, start_date, end_date))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"error": f"No data for segment {segment_key}={segment_value}"}

        row_dict = dict(row)
        total = row_dict['total_decisions'] or 0
        correct = row_dict['correct_decisions'] or 0

        return {
            "segment_key": segment_key,
            "segment_value": segment_value,
            "total_decisions": total,
            "correct_decisions": correct,
            "accuracy": (correct / total * 100) if total > 0 else 0,
            "avg_confidence": row_dict['avg_confidence'] or 0,
            "escalation_rate": (row_dict['escalated_count'] / total * 100) if total > 0 else 0,
            "override_rate": (row_dict['override_count'] / total * 100) if total > 0 else 0,
        }

    def calculate_demographic_parity(self, start_date: str, end_date: str,
                                    segment_key: str = 'department') -> List[FairnessMetric]:
        """
        Calculate demographic parity (accuracy variance across groups)
        Target: ±10% variance
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        segment_column_map = {
            'department': 'user_department',
            'category': 'incident_category',
            'severity': 'severity_level'
        }
        segment_column = segment_column_map.get(segment_key, segment_key)

        # Get accuracy by segment
        query = f"""
        SELECT
            {segment_column} as segment,
            COUNT(*) as total,
            SUM(CASE WHEN was_aria_correct = 1 THEN 1 ELSE 0 END) as correct
        FROM aria_audit_log
        WHERE timestamp_utc BETWEEN ? AND ?
        GROUP BY {segment_column}
        HAVING COUNT(*) > 5
        """

        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        # Calculate accuracy per segment
        accuracies = []
        for row in rows:
            row_dict = dict(row)
            total = row_dict['total']
            correct = row_dict['correct']
            accuracy = (correct / total * 100) if total > 0 else 0
            accuracies.append({
                'segment': row_dict['segment'],
                'accuracy': accuracy,
                'total': total
            })

        # Calculate overall average and variance
        avg_accuracy = sum(acc['accuracy'] for acc in accuracies) / len(accuracies)
        threshold = self.fairness_thresholds['demographic_parity']

        # Calculate fairness metrics for each segment
        metrics = []
        for acc_data in accuracies:
            variance = abs(acc_data['accuracy'] - avg_accuracy)
            variance_pct = (variance / avg_accuracy * 100) if avg_accuracy > 0 else 0

            status = "PASS" if variance_pct <= (threshold * 100) else "WARNING" if variance_pct <= (threshold * 150) else "FAIL"

            metrics.append(FairnessMetric(
                metric_name="Demographic Parity",
                segment=f"{segment_key}={acc_data['segment']}",
                value=acc_data['accuracy'],
                target_value=avg_accuracy,
                status=status,
                variance_percentage=variance_pct
            ))

        return metrics

    def calculate_equalized_odds(self, start_date: str, end_date: str) -> List[FairnessMetric]:
        """
        Calculate equalized odds (true positive rate across groups)
        Target: ±10% variance
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get true positive rate by category
        query = """
        SELECT
            incident_category,
            COUNT(*) as total,
            SUM(CASE WHEN was_aria_correct = 1 AND was_auto_resolved = 1 THEN 1 ELSE 0 END) as tp,
            SUM(CASE WHEN was_aria_correct = 1 THEN 1 ELSE 0 END) as correct
        FROM aria_audit_log
        WHERE timestamp_utc BETWEEN ? AND ?
        GROUP BY incident_category
        HAVING COUNT(*) > 5
        """

        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        # Calculate TPR per category
        tprs = []
        for row in rows:
            row_dict = dict(row)
            total = row_dict['total']
            correct = row_dict['correct'] or 1  # Avoid division by zero
            tp_rate = (row_dict['tp'] / correct * 100) if correct > 0 else 0
            tprs.append({
                'category': row_dict['incident_category'],
                'tpr': tp_rate,
                'total': total
            })

        avg_tpr = sum(tpr['tpr'] for tpr in tprs) / len(tprs) if tprs else 0
        threshold = self.fairness_thresholds['equalized_odds']

        metrics = []
        for tpr_data in tprs:
            variance = abs(tpr_data['tpr'] - avg_tpr)
            variance_pct = (variance / avg_tpr * 100) if avg_tpr > 0 else 0

            status = "PASS" if variance_pct <= (threshold * 100) else "WARNING" if variance_pct <= (threshold * 150) else "FAIL"

            metrics.append(FairnessMetric(
                metric_name="Equalized Odds (TPR)",
                segment=f"category={tpr_data['category']}",
                value=tpr_data['tpr'],
                target_value=avg_tpr,
                status=status,
                variance_percentage=variance_pct
            ))

        return metrics

    def calculate_calibration(self, start_date: str, end_date: str) -> FairnessMetric:
        """
        Calculate calibration (confidence scores match reality)
        Target: ±5% variance
        Checks if confidence score correlates with actual accuracy
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
        SELECT
            ROUND(confidence_score, -1) as confidence_bucket,
            COUNT(*) as total,
            SUM(CASE WHEN was_aria_correct = 1 THEN 1 ELSE 0 END) as correct
        FROM aria_audit_log
        WHERE timestamp_utc BETWEEN ? AND ?
        AND confidence_score IS NOT NULL
        GROUP BY ROUND(confidence_score, -1)
        ORDER BY confidence_bucket
        """

        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        # Calculate calibration error
        total_variance = 0
        count = 0

        for row in rows:
            row_dict = dict(row)
            confidence_bucket = row_dict['confidence_bucket']
            total = row_dict['total']
            correct = row_dict['correct']
            actual_accuracy = (correct / total * 100) if total > 0 else 0

            variance = abs(confidence_bucket - actual_accuracy)
            total_variance += variance
            count += 1

        avg_calibration_error = (total_variance / count) if count > 0 else 0
        threshold = self.fairness_thresholds['calibration']
        threshold_pct = threshold * 100

        status = "PASS" if avg_calibration_error <= threshold_pct else "WARNING" if avg_calibration_error <= (threshold_pct * 1.5) else "FAIL"

        return FairnessMetric(
            metric_name="Calibration",
            segment="overall",
            value=avg_calibration_error,
            target_value=threshold_pct,
            status=status,
            variance_percentage=avg_calibration_error
        )

    def generate_monthly_fairness_report(self, year: int, month: int) -> Dict[str, Any]:
        """Generate comprehensive monthly fairness report"""
        # Date range
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"

        # Calculate all metrics
        dept_parity = self.calculate_demographic_parity(start_date, end_date, 'department')
        category_parity = self.calculate_demographic_parity(start_date, end_date, 'category')
        equalized_odds = self.calculate_equalized_odds(start_date, end_date)
        calibration = self.calculate_calibration(start_date, end_date)

        # Determine overall status
        all_metrics = dept_parity + category_parity + equalized_odds
        if calibration:
            all_metrics.append(calibration)

        failed_metrics = [m for m in all_metrics if m.status == "FAIL"]
        warning_metrics = [m for m in all_metrics if m.status == "WARNING"]

        overall_status = "FAIL" if failed_metrics else "WARNING" if warning_metrics else "PASS"

        return {
            "report_date": datetime.now().isoformat(),
            "report_period": f"{year}-{month:02d}",
            "overall_status": overall_status,
            "metrics_summary": {
                "total_metrics": len(all_metrics),
                "passed": len([m for m in all_metrics if m.status == "PASS"]),
                "warnings": len(warning_metrics),
                "failures": len(failed_metrics)
            },
            "detailed_metrics": {
                "demographic_parity_by_department": [asdict(m) for m in dept_parity],
                "demographic_parity_by_category": [asdict(m) for m in category_parity],
                "equalized_odds": [asdict(m) for m in equalized_odds],
                "calibration": asdict(calibration) if calibration else None
            },
            "findings": {
                "passed_metrics": [m.metric_name for m in all_metrics if m.status == "PASS"],
                "warning_metrics": [m.metric_name for m in warning_metrics],
                "failed_metrics": [m.metric_name for m in failed_metrics]
            },
            "recommendations": self._generate_recommendations(failed_metrics, warning_metrics)
        }

    def _generate_recommendations(self, failed: List[FairnessMetric],
                                 warnings: List[FairnessMetric]) -> List[str]:
        """Generate remediation recommendations"""
        recommendations = []

        for metric in failed:
            if "Demographic Parity" in metric.metric_name:
                recommendations.append(f"⚠️  CRITICAL: Demographic parity failed for {metric.segment}. Retrain model with balanced data samples.")
            elif "Equalized Odds" in metric.metric_name:
                recommendations.append(f"⚠️  CRITICAL: True positive rate imbalance detected for {metric.segment}. Review decision logic.")
            elif "Calibration" in metric.metric_name:
                recommendations.append("⚠️  CRITICAL: Confidence scores don't match actual accuracy. Adjust confidence thresholds.")

        for metric in warnings:
            if "Demographic Parity" in metric.metric_name:
                recommendations.append(f"⚠️  WARNING: Minor demographic parity variance for {metric.segment}. Monitor closely.")
            elif "Equalized Odds" in metric.metric_name:
                recommendations.append(f"⚠️  WARNING: Minor TPR imbalance for {metric.segment}. Consider additional training data.")

        if not recommendations:
            recommendations.append("✅ All fairness metrics within acceptable thresholds. Continue regular monitoring.")

        return recommendations

def asdict(obj):
    """Convert dataclass to dict"""
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return obj

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    bias_service = BiasDetectionService()

    # Generate monthly fairness report
    report = bias_service.generate_monthly_fairness_report(2026, 3)
    print(f"\n📊 FAIRNESS REPORT:\n{json.dumps(report, indent=2, default=str)}")

