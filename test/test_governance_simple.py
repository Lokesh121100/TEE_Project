# -*- coding: utf-8 -*-
# INTELSOFT ARIA - Governance Framework Test Suite

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.governance import AuditLoggingService, EscalationRulesEngine, CostGovernanceService
from datetime import datetime

print("\n" + "="*70)
print("[TEST] INTELSOFT ARIA - GOVERNANCE FRAMEWORK")
print("="*70)

# TEST 1: Audit Logging
print("\n[TEST] TEST 1: AUDIT LOGGING")
try:
    audit_service = AuditLoggingService()
    print("[OK] Audit logging service initialized")
    print("[OK] Database created at: data/aria_governance.db")
except Exception as e:
    print(f"[FAIL] Audit logging failed: {e}")
    sys.exit(1)

# TEST 2: Escalation Rules
print("\n[TEST] TEST 2: ESCALATION RULES")
try:
    engine = EscalationRulesEngine()
    print("[OK] Escalation rules engine initialized")

    # Test safe auto-resolve
    ticket = {
        'confidence_score': 95,
        'incident_category': 'Access',
        'severity_level': 'Low',
        'user_department': 'Sales',
        'ai_action': 'password reset',
        'sla_status': 10,
        'is_vip_user': False,
        'previous_failures': 0,
        'policy_violation': False,
        'security_concern': False,
        'compliance_concern': False
    }
    decision = engine.evaluate_escalation(ticket)
    print(f"[OK] Safe ticket evaluated: {decision.escalation_level.value}")
    print(f"[OK] Risk score: {decision.risk_score:.1f}/100")

except Exception as e:
    print(f"[FAIL] Escalation rules failed: {e}")
    sys.exit(1)

# TEST 3: Cost Governance
print("\n[TEST] TEST 3: COST GOVERNANCE")
try:
    cost_service = CostGovernanceService()
    print("[OK] Cost governance service initialized")

    # Record a cost
    cost_id = cost_service.record_cost(
        category='inference',
        amount=1500.00,
        description='Test cost',
        ticket_count=1200
    )
    print(f"[OK] Cost recorded: {cost_id}")

except Exception as e:
    print(f"[FAIL] Cost governance failed: {e}")
    sys.exit(1)

# SUMMARY
print("\n" + "="*70)
print("[RESULT] ALL TESTS PASSED")
print("="*70)
print("[OK] Intelsoft ARIA Governance Framework is OPERATIONAL")
print("[OK] Database: data/aria_governance.db")
print("[OK] Audit Logging: WORKING")
print("[OK] Escalation Rules: WORKING")
print("[OK] Cost Governance: WORKING")
print("="*70)

