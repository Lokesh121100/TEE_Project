# 🚨 ARIA Governance - Escalation Rules Engine
# Smart escalation logic based on risk factors

import sqlite3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

class EscalationLevel(Enum):
    AUTO_RESOLVE = "auto_resolve"
    AI_ASSIST = "ai_assist"
    STANDARD_ESCALATE = "standard_escalate"
    URGENT_ESCALATE = "urgent_escalate"
    CRITICAL_ESCALATE = "critical_escalate"

class EscalationTeam(Enum):
    NONE = "none"
    STANDARD_QUEUE = "standard_queue"
    PRIORITY_QUEUE = "priority_queue"
    URGENT_QUEUE = "urgent_queue"
    NETWORK_TEAM = "network_team"
    SECURITY_TEAM = "security_team"
    COMPLIANCE_TEAM = "compliance_team"
    VIP_TEAM = "vip_team"

@dataclass
class EscalationDecision:
    """Result of escalation rule evaluation"""
    should_escalate: bool
    escalation_level: EscalationLevel
    escalation_team: EscalationTeam
    sla_minutes: int
    reasoning: str
    risk_score: float  # 0-100
    triggered_rules: List[str]

class EscalationRulesEngine:
    """Engine for determining when to escalate ARIA decisions to humans"""

    def __init__(self, db_path: str = "data/aria_governance.db"):
        self.db_path = db_path

    def evaluate_escalation(self, ticket_data: Dict) -> EscalationDecision:
        """
        Evaluate whether a ticket should be escalated

        ticket_data should contain:
        - confidence_score (0-100)
        - incident_category
        - severity_level
        - user_department
        - ai_action (suggested action)
        - sla_status (% elapsed)
        """
        triggered_rules = []
        risk_score = 0

        # RULE 1: Confidence too low
        confidence = ticket_data.get('confidence_score', 0)
        if confidence < 50:
            triggered_rules.append("CONFIDENCE_CRITICAL_LOW")
            risk_score += 40
        elif confidence < 85:
            triggered_rules.append("CONFIDENCE_BELOW_THRESHOLD")
            risk_score += 25
        elif confidence < 75:
            triggered_rules.append("CONFIDENCE_MARGINAL")
            risk_score += 10

        # RULE 2: Critical severity always escalates
        severity = ticket_data.get('severity_level', 'Medium')
        if severity.lower() == 'critical':
            triggered_rules.append("CRITICAL_SEVERITY")
            risk_score += 50
        elif severity.lower() == 'high':
            triggered_rules.append("HIGH_SEVERITY")
            risk_score += 20

        # RULE 3: High-risk actions require escalation
        action = ticket_data.get('ai_action', '').lower()
        high_risk_actions = [
            'account suspension', 'account deletion', 'password reset',
            'system change', 'data deletion', 'access grant',
            'permission change', 'service disable'
        ]
        if any(action in risk_action for risk_action in high_risk_actions):
            triggered_rules.append("HIGH_RISK_ACTION")
            risk_score += 45

        # RULE 4: Policy violations
        if ticket_data.get('policy_violation', False):
            triggered_rules.append("POLICY_VIOLATION")
            risk_score += 35

        # RULE 5: Security/Compliance concerns
        if ticket_data.get('security_concern', False):
            triggered_rules.append("SECURITY_CONCERN")
            risk_score += 50

        if ticket_data.get('compliance_concern', False):
            triggered_rules.append("COMPLIANCE_CONCERN")
            risk_score += 50

        # RULE 6: SLA at risk
        sla_status = ticket_data.get('sla_status', 0)
        if sla_status > 90:
            triggered_rules.append("SLA_CRITICAL")
            risk_score += 40
        elif sla_status > 75:
            triggered_rules.append("SLA_AT_RISK")
            risk_score += 20

        # RULE 7: VIP user
        if ticket_data.get('is_vip_user', False):
            triggered_rules.append("VIP_USER")
            risk_score += 15

        # RULE 8: Multiple failures
        failure_count = ticket_data.get('previous_failures', 0)
        if failure_count >= 3:
            triggered_rules.append("MULTIPLE_FAILURES")
            risk_score += 35
        elif failure_count == 2:
            triggered_rules.append("REPEATED_ISSUE")
            risk_score += 20

        # RULE 9: Unknown category
        category = ticket_data.get('incident_category', '')
        known_categories = ['Access', 'Network', 'Hardware', 'Software', 'Critical']
        if category not in known_categories:
            triggered_rules.append("UNKNOWN_CATEGORY")
            risk_score += 30

        # Determine escalation decision
        return self._make_escalation_decision(risk_score, triggered_rules, ticket_data)

    def _make_escalation_decision(self, risk_score: float,
                                 triggered_rules: List[str],
                                 ticket_data: Dict) -> EscalationDecision:
        """Make final escalation decision based on risk score"""

        # CRITICAL (>80): Immediate escalation
        if risk_score > 80:
            severity = ticket_data.get('severity_level', 'High')
            if severity.lower() == 'critical':
                team = EscalationTeam.SECURITY_TEAM if 'SECURITY_CONCERN' in triggered_rules else EscalationTeam.URGENT_QUEUE
                sla = 5
            else:
                team = EscalationTeam.URGENT_QUEUE
                sla = 15

            return EscalationDecision(
                should_escalate=True,
                escalation_level=EscalationLevel.CRITICAL_ESCALATE,
                escalation_team=team,
                sla_minutes=sla,
                reasoning=f"Critical risk detected ({risk_score:.1f}/100). Immediate human escalation required.",
                risk_score=risk_score,
                triggered_rules=triggered_rules
            )

        # HIGH (60-80): Urgent escalation
        if risk_score > 60:
            sla = 30 if ticket_data.get('is_vip_user') else 60
            return EscalationDecision(
                should_escalate=True,
                escalation_level=EscalationLevel.URGENT_ESCALATE,
                escalation_team=EscalationTeam.PRIORITY_QUEUE,
                sla_minutes=sla,
                reasoning=f"High risk detected ({risk_score:.1f}/100). Urgent escalation to priority queue.",
                risk_score=risk_score,
                triggered_rules=triggered_rules
            )

        # MEDIUM (40-60): Standard escalation
        if risk_score > 40:
            return EscalationDecision(
                should_escalate=True,
                escalation_level=EscalationLevel.STANDARD_ESCALATE,
                escalation_team=EscalationTeam.STANDARD_QUEUE,
                sla_minutes=120,
                reasoning=f"Moderate risk detected ({risk_score:.1f}/100). Standard escalation to queue.",
                risk_score=risk_score,
                triggered_rules=triggered_rules
            )

        # LOW-MEDIUM (20-40): AI-assist (human verifies)
        if risk_score > 20:
            return EscalationDecision(
                should_escalate=False,
                escalation_level=EscalationLevel.AI_ASSIST,
                escalation_team=EscalationTeam.NONE,
                sla_minutes=300,
                reasoning=f"Low-moderate risk ({risk_score:.1f}/100). AI-assisted mode - human verification recommended.",
                risk_score=risk_score,
                triggered_rules=triggered_rules
            )

        # AUTO-RESOLVE: Safe to auto-resolve
        return EscalationDecision(
            should_escalate=False,
            escalation_level=EscalationLevel.AUTO_RESOLVE,
            escalation_team=EscalationTeam.NONE,
            sla_minutes=0,
            reasoning=f"Low risk ({risk_score:.1f}/100). Safe to auto-resolve.",
            risk_score=risk_score,
            triggered_rules=triggered_rules
        )

    def get_escalation_team_assignment(self, escalation_decision: EscalationDecision,
                                      ticket_data: Dict) -> str:
        """Determine which team should handle the escalation"""

        # Category-based routing
        category = ticket_data.get('incident_category', '').lower()

        if escalation_decision.escalation_team == EscalationTeam.SECURITY_TEAM:
            return "Security Team"

        if escalation_decision.escalation_team == EscalationTeam.COMPLIANCE_TEAM:
            return "Compliance Team"

        if escalation_decision.escalation_team == EscalationTeam.VIP_TEAM:
            return "VIP Support Team"

        # Route by category
        category_routes = {
            'network': 'Network Support Team',
            'vpn': 'Network Support Team',
            'hardware': 'Hardware Support Team',
            'software': 'Software Support Team',
            'access': 'Access Control Team',
            'critical': 'Incident Management Team'
        }

        for cat_key, team_name in category_routes.items():
            if cat_key in category:
                return team_name

        # Default routing
        if escalation_decision.escalation_level == EscalationLevel.CRITICAL_ESCALATE:
            return "Incident Management Team"
        elif escalation_decision.escalation_level == EscalationLevel.URGENT_ESCALATE:
            return "Priority Support Team"
        else:
            return "Service Desk Team"

    def store_escalation_rule(self, rule_name: str, condition: str,
                            escalation_team: str, sla_minutes: int,
                            priority: str = "Medium") -> bool:
        """Store an escalation rule in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO aria_escalation_rules
                (rule_id, rule_name, condition, escalation_team, sla_minutes, priority, active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (rule_name.lower().replace(' ', '_'), rule_name, condition, escalation_team, sla_minutes, priority))

            conn.commit()
            return True
        finally:
            conn.close()

    def get_active_escalation_rules(self) -> List[Dict]:
        """Get all active escalation rules"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM aria_escalation_rules WHERE active = 1 ORDER BY priority DESC")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    engine = EscalationRulesEngine()

    # Test escalation scenario 1: Low confidence VPN issue
    ticket1 = {
        'confidence_score': 45,  # Below threshold
        'incident_category': 'Network',
        'severity_level': 'High',
        'user_department': 'Engineering',
        'ai_action': 'Try VPN restart',
        'sla_status': 20,
        'is_vip_user': False,
        'previous_failures': 0,
        'policy_violation': False,
        'security_concern': False,
        'compliance_concern': False
    }

    decision1 = engine.evaluate_escalation(ticket1)
    print(f"\n🎯 SCENARIO 1: Low Confidence\n{json.dumps(decision1.__dict__, indent=2, default=str)}")

    # Test escalation scenario 2: Critical severity
    ticket2 = {
        'confidence_score': 92,  # High confidence
        'incident_category': 'Critical',
        'severity_level': 'Critical',
        'user_department': 'Finance',
        'ai_action': 'immediate escalation',
        'sla_status': 85,  # SLA at risk
        'is_vip_user': True,
        'previous_failures': 2,
        'policy_violation': False,
        'security_concern': True,  # Security concern
        'compliance_concern': False
    }

    decision2 = engine.evaluate_escalation(ticket2)
    team2 = engine.get_escalation_team_assignment(decision2, ticket2)
    print(f"\n🎯 SCENARIO 2: Critical + Security\n{json.dumps(decision2.__dict__, indent=2, default=str)}\nAssigned to: {team2}")

    # Test escalation scenario 3: Safe auto-resolve
    ticket3 = {
        'confidence_score': 95,  # Very high confidence
        'incident_category': 'Access',
        'severity_level': 'Low',
        'user_department': 'Sales',
        'ai_action': 'password reset instructions sent',
        'sla_status': 5,
        'is_vip_user': False,
        'previous_failures': 0,
        'policy_violation': False,
        'security_concern': False,
        'compliance_concern': False
    }

    decision3 = engine.evaluate_escalation(ticket3)
    print(f"\n🎯 SCENARIO 3: Safe Auto-Resolve\n{json.dumps(decision3.__dict__, indent=2, default=str)}")

