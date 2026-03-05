# 🛡️ ARIA Governance - Audit Logging System
# Comprehensive logging for every ARIA decision with audit trails

import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path

# ============================================================================
# DATABASE SCHEMA
# ============================================================================

AUDIT_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS aria_audit_log (
    -- Primary Key
    log_id TEXT PRIMARY KEY,
    timestamp_utc TEXT NOT NULL,

    -- DECISION CONTEXT
    ticket_id TEXT NOT NULL,
    incident_category TEXT NOT NULL,
    incident_subcategory TEXT,
    severity_level TEXT,
    user_department TEXT,
    incident_description TEXT,

    -- AI DECISION
    model_version TEXT NOT NULL,
    suggested_category TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    suggested_action TEXT,
    suggested_priority TEXT,
    recommended_escalation_path TEXT,
    decision_reasoning TEXT,

    -- GUARDRAILS APPLIED
    confidence_check_passed INTEGER,
    hallucination_check_passed INTEGER,
    policy_constraint_check_passed INTEGER,
    knowledge_base_validation_passed INTEGER,
    fairness_check_passed INTEGER,

    -- HUMAN OVERRIDE
    was_overridden INTEGER DEFAULT 0,
    override_reason TEXT,
    human_user_id TEXT,
    override_timestamp_utc TEXT,
    human_confirmed_category TEXT,

    -- ACTION TAKEN
    was_auto_resolved INTEGER DEFAULT 0,
    was_escalated INTEGER DEFAULT 0,
    escalation_reason TEXT,
    assignment_team TEXT,
    sla_target_minutes INTEGER,
    ticket_status TEXT,

    -- OUTCOME
    final_status TEXT,
    resolution_time_minutes REAL,
    user_satisfaction_score REAL,
    was_aria_correct INTEGER,
    improvement_opportunity INTEGER,

    -- SYSTEM FIELDS
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    data_hash TEXT
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_ticket_id ON aria_audit_log(ticket_id);
CREATE INDEX IF NOT EXISTS idx_timestamp ON aria_audit_log(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_category ON aria_audit_log(incident_category);
CREATE INDEX IF NOT EXISTS idx_confidence ON aria_audit_log(confidence_score);
CREATE INDEX IF NOT EXISTS idx_escalation ON aria_audit_log(was_escalated);

-- Compliance/Fairness metrics table
CREATE TABLE IF NOT EXISTS aria_fairness_metrics (
    metric_id TEXT PRIMARY KEY,
    report_date TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    segment TEXT NOT NULL,
    value REAL NOT NULL,
    target_value REAL,
    status TEXT,  -- PASS / WARNING / FAIL
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Cost tracking table
CREATE TABLE IF NOT EXISTS aria_cost_tracking (
    cost_id TEXT PRIMARY KEY,
    date_utc TEXT NOT NULL,
    category TEXT NOT NULL,  -- INFERENCE, STORAGE, INFRASTRUCTURE, OPERATIONS
    amount DECIMAL(10, 2) NOT NULL,
    description TEXT,
    ticket_count INTEGER,
    cost_per_ticket DECIMAL(10, 4),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Escalation rules table
CREATE TABLE IF NOT EXISTS aria_escalation_rules (
    rule_id TEXT PRIMARY KEY,
    rule_name TEXT NOT NULL,
    condition TEXT NOT NULL,
    escalation_team TEXT NOT NULL,
    sla_minutes INTEGER,
    priority TEXT,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

# ============================================================================
# DATA MODELS
# ============================================================================

class ConfidenceCheckStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"

class AuditDecisionType(Enum):
    AUTO_RESOLVED = "auto_resolved"
    AI_ASSISTED = "ai_assisted"
    ESCALATED = "escalated"
    HUMAN_HANDLED = "human_handled"

@dataclass
class GuardrailChecks:
    """Guardrail validation results"""
    confidence_check_passed: bool
    hallucination_check_passed: bool
    policy_constraint_check_passed: bool
    knowledge_base_validation_passed: bool
    fairness_check_passed: bool

    def all_passed(self) -> bool:
        """Check if all guardrails passed"""
        return all([
            self.confidence_check_passed,
            self.hallucination_check_passed,
            self.policy_constraint_check_passed,
            self.knowledge_base_validation_passed,
            self.fairness_check_passed
        ])

    def get_failed_checks(self) -> List[str]:
        """Get list of failed checks"""
        failed = []
        if not self.confidence_check_passed:
            failed.append("confidence_check")
        if not self.hallucination_check_passed:
            failed.append("hallucination_check")
        if not self.policy_constraint_check_passed:
            failed.append("policy_constraint_check")
        if not self.knowledge_base_validation_passed:
            failed.append("knowledge_base_validation")
        if not self.fairness_check_passed:
            failed.append("fairness_check")
        return failed

@dataclass
class AuditLogEntry:
    """Complete audit log entry for ARIA decision"""
    log_id: str
    timestamp_utc: str
    ticket_id: str
    incident_category: str
    confidence_score: float
    model_version: str
    suggested_category: str
    suggested_action: str
    guardrails: GuardrailChecks
    was_auto_resolved: bool
    was_escalated: bool
    assignment_team: Optional[str] = None
    incident_subcategory: Optional[str] = None
    severity_level: Optional[str] = None
    user_department: Optional[str] = None
    incident_description: Optional[str] = None
    suggested_priority: Optional[str] = None
    recommended_escalation_path: Optional[str] = None
    decision_reasoning: Optional[str] = None
    escalation_reason: Optional[str] = None
    sla_target_minutes: Optional[int] = None
    ticket_status: Optional[str] = None
    was_overridden: bool = False
    human_user_id: Optional[str] = None
    override_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = asdict(self)
        # Convert guardrails to individual fields
        guardrails = data.pop('guardrails')
        data['confidence_check_passed'] = guardrails.get('confidence_check_passed', False)
        data['hallucination_check_passed'] = guardrails.get('hallucination_check_passed', False)
        data['policy_constraint_check_passed'] = guardrails.get('policy_constraint_check_passed', False)
        data['knowledge_base_validation_passed'] = guardrails.get('knowledge_base_validation_passed', False)
        data['fairness_check_passed'] = guardrails.get('fairness_check_passed', False)
        return data

# ============================================================================
# AUDIT LOGGING SERVICE
# ============================================================================

class AuditLoggingService:
    """Service for logging and retrieving ARIA audit trails"""

    def __init__(self, db_path: str = "data/aria_governance.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database with schema"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(AUDIT_LOG_SCHEMA)
        conn.commit()
        conn.close()
        print(f"[OK] Audit database initialized: {self.db_path}")

    def log_decision(self, entry: AuditLogEntry) -> str:
        """Log an ARIA decision to audit trail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Generate log ID if not provided
        if not entry.log_id:
            entry.log_id = str(uuid.uuid4())

        # Convert entry to database format
        data = entry.to_dict()

        # Calculate data hash for integrity
        data_hash = self._calculate_hash(entry.ticket_id, entry.confidence_score, entry.suggested_category)
        data['data_hash'] = data_hash

        # Insert into database
        columns = list(data.keys())
        placeholders = ', '.join(['?' for _ in columns])
        query = f"INSERT INTO aria_audit_log ({', '.join(columns)}) VALUES ({placeholders})"

        try:
            cursor.execute(query, [data.get(col) for col in columns])
            conn.commit()
            print(f"✅ Audit log created: {entry.log_id}")
            return entry.log_id
        except Exception as e:
            print(f"❌ Error logging decision: {e}")
            return None
        finally:
            conn.close()

    def get_decision_log(self, log_id: str) -> Optional[Dict]:
        """Retrieve a specific audit log entry"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM aria_audit_log WHERE log_id = ?", (log_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_logs_by_ticket(self, ticket_id: str) -> List[Dict]:
        """Get all logs for a specific ticket"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM aria_audit_log WHERE ticket_id = ? ORDER BY timestamp_utc DESC", (ticket_id,))
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_logs_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get logs within a date range"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM aria_audit_log WHERE timestamp_utc BETWEEN ? AND ? ORDER BY timestamp_utc DESC",
            (start_date, end_date)
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_escalations(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """Get all escalated tickets"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if start_date and end_date:
            cursor.execute(
                "SELECT * FROM aria_audit_log WHERE was_escalated = 1 AND timestamp_utc BETWEEN ? AND ? ORDER BY timestamp_utc DESC",
                (start_date, end_date)
            )
        else:
            cursor.execute("SELECT * FROM aria_audit_log WHERE was_escalated = 1 ORDER BY timestamp_utc DESC")

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_accuracy_metrics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Calculate accuracy metrics for a date range"""
        logs = self.get_logs_by_date_range(start_date, end_date)

        if not logs:
            return {"error": "No logs found"}

        total = len(logs)
        correct = sum(1 for log in logs if log.get('was_aria_correct') == 1)
        auto_resolved = sum(1 for log in logs if log.get('was_auto_resolved') == 1)
        escalated = sum(1 for log in logs if log.get('was_escalated') == 1)
        overridden = sum(1 for log in logs if log.get('was_overridden') == 1)

        avg_confidence = sum(log.get('confidence_score', 0) for log in logs) / total if total > 0 else 0

        return {
            "total_decisions": total,
            "correct_decisions": correct,
            "accuracy_percentage": (correct / total * 100) if total > 0 else 0,
            "auto_resolved_count": auto_resolved,
            "auto_resolved_percentage": (auto_resolved / total * 100) if total > 0 else 0,
            "escalated_count": escalated,
            "escalated_percentage": (escalated / total * 100) if total > 0 else 0,
            "human_override_count": overridden,
            "human_override_percentage": (overridden / total * 100) if total > 0 else 0,
            "average_confidence_score": avg_confidence,
        }

    def _calculate_hash(self, ticket_id: str, confidence: float, category: str) -> str:
        """Calculate hash for data integrity verification"""
        data = f"{ticket_id}:{confidence}:{category}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Initialize audit service
    audit_service = AuditLoggingService()

    # Create sample audit log entry
    guardrails = GuardrailChecks(
        confidence_check_passed=True,
        hallucination_check_passed=True,
        policy_constraint_check_passed=True,
        knowledge_base_validation_passed=True,
        fairness_check_passed=True
    )

    entry = AuditLogEntry(
        log_id=str(uuid.uuid4()),
        timestamp_utc=datetime.utcnow().isoformat(),
        ticket_id="TICK-001",
        incident_category="Network",
        incident_subcategory="VPN",
        confidence_score=92.5,
        model_version="llama3-70b-v2.1",
        suggested_category="Network/VPN",
        suggested_action="Try VPN client restart",
        guardrails=guardrails,
        was_auto_resolved=True,
        was_escalated=False,
        assignment_team="Network Support",
        severity_level="Medium",
        user_department="Engineering",
        incident_description="Cannot connect to VPN",
        suggested_priority="High",
        decision_reasoning="Matched KB article #2341 with 92% confidence"
    )

    # Log the decision
    log_id = audit_service.log_decision(entry)

    # Retrieve the log
    if log_id:
        log = audit_service.get_decision_log(log_id)
        print(f"\n📋 Logged Decision:\n{json.dumps(log, indent=2, default=str)}")

    # Get accuracy metrics
    start = "2026-03-01"
    end = "2026-03-31"
    metrics = audit_service.get_accuracy_metrics(start, end)
    print(f"\n📊 Accuracy Metrics:\n{json.dumps(metrics, indent=2)}")

