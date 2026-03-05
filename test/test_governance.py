# -*- coding: utf-8 -*-
# INTELSOFT ARIA - Governance Framework Test Suite

import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.governance import (
    AuditLoggingService,
    AuditLogEntry,
    GuardrailChecks,
    BiasDetectionService,
    EscalationRulesEngine,
    CostGovernanceService
)

def test_audit_logging():
    print("
" + "="*70)
    print("[TEST] TEST 1: AUDIT LOGGING SERVICE")
    print("="*70)

    audit_service = AuditLoggingService()
    print("[OK] Audit logging service initialized")

    print("
[INFO] Test 1.1: Logging a decision...")
    guardrails = GuardrailChecks(
        confidence_check_passed=True,
        hallucination_check_passed=True,
        policy_constraint_check_passed=True,
        knowledge_base_validation_passed=True,
        fairness_check_passed=True
    )

    entry = AuditLogEntry(
        log_id="",
        timestamp_utc=datetime.utcnow().isoformat(),
        ticket_id="INTELSOFT-TICK-001",
        incident_category="Network",
        confidence_score=92.5,
        model_version="llama3-70b-v2.1",
        suggested_category="Network/VPN",
        suggested_action="Restart VPN client",
        guardrails=guardrails,
        was_auto_resolved=True,
        was_escalated=False,
        severity_level="Medium",
        user_department="Engineering",
        incident_description="Cannot connect to VPN"
    )

    log_id = audit_service.log_decision(entry)
    if log_id:
        print(f"[OK] Decision logged: {log_id}")
    else:
        print("[FAIL] Failed to log decision")
        return False

    print("
[INFO] Test 1.2: Retrieving logged decision...")
    retrieved_log = audit_service.get_decision_log(log_id)
    if retrieved_log:
        print(f"[OK] Successfully retrieved log for ticket: {retrieved_log['ticket_id']}")
    else:
        print("[FAIL] Failed to retrieve log")
        return False

    print("
[OK] AUDIT LOGGING TEST PASSED")
    return True

def test_escalation_rules():
    print("
" + "="*70)
    print("[TEST] TEST 2: ESCALATION RULES ENGINE")
    print("="*70)

    engine = EscalationRulesEngine()
    print("[OK] Escalation rules engine initialized")

    print("
[INFO] Test 2.1: Safe auto-resolve scenario...")
    ticket1 = {
        'confidence_score': 95,
        'incident_category': 'Access',
        'severity_level': 'Low',
        'user_department': 'Sales',
        'ai_action': 'password reset instructions',
        'sla_status': 10,
        'is_vip_user': False,
        'previous_failures': 0,
        'policy_violation': False,
        'security_concern': False,
        'compliance_concern': False
    }

    decision1 = engine.evaluate_escalation(ticket1)
    print(f"[OK] Escalation level: {decision1.escalation_level.value}")
    print(f"[OK] Risk score: {decision1.risk_score:.1f}/100")

    if decision1.escalation_level.value == 'auto_resolve':
        print("[OK] Correctly identified as safe for auto-resolution")
    else:
        print("[FAIL] Wrong escalation decision")
        return False

    print("
[INFO] Test 2.2: Critical escalation scenario...")
    ticket2 = {
        'confidence_score': 45,
        'incident_category': 'Critical',
        'severity_level': 'Critical',
        'user_department': 'Finance',
        'ai_action': 'system restart',
        'sla_status': 85,
        'is_vip_user': True,
        'previous_failures': 2,
        'policy_violation': False,
        'security_concern': True,
        'compliance_concern': False
    }

    decision2 = engine.evaluate_escalation(ticket2)
    print(f"[OK] Escalation level: {decision2.escalation_level.value}")
    print(f"[OK] Risk score: {decision2.risk_score:.1f}/100")

    if decision2.should_escalate:
        print("[OK] Correctly identified as critical escalation")
    else:
        print("[FAIL] Wrong escalation decision")
        return False

    print("
[OK] ESCALATION RULES TEST PASSED")
    return True

def test_cost_governance():
    print("
" + "="*70)
    print("[TEST] TEST 3: COST GOVERNANCE SERVICE")
    print("="*70)

    cost_service = CostGovernanceService()
    print("[OK] Cost governance service initialized")

    print("
[INFO] Test 3.1: Recording costs...")
    cost_id = cost_service.record_cost(
        category='inference',
        amount=1500.00,
        description='March 2026 inference costs',
        ticket_count=1200
    )
    print(f"[OK] Cost recorded: {cost_id}")

    print("
[OK] COST GOVERNANCE TEST PASSED")
    return True

def test_database():
    print("
" + "="*70)
    print("[TEST] TEST 4: DATABASE INTEGRITY")
    print("="*70)

    db_path = "data/aria_governance.db"
    
    if Path(db_path).exists():
        print(f"[OK] Database file exists: {db_path}")
    else:
        print(f"[FAIL] Database file not found")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    conn.close()

    expected = ['aria_audit_log', 'aria_fairness_metrics', 'aria_cost_tracking', 'aria_escalation_rules']
    for table in expected:
        if table in tables:
            print(f"[OK] Table exists: {table}")
        else:
            print(f"[FAIL] Table missing: {table}")
            return False

    print("
[OK] DATABASE INTEGRITY TEST PASSED")
    return True

def run_all_tests():
    print("
" + "="*70)
    print("[TEST] INTELSOFT ARIA - GOVERNANCE FRAMEWORK TEST SUITE")
    print("="*70)

    results = {}
    
    try:
        results['database'] = test_database()
    except Exception as e:
        print(f"[FAIL] Database test error: {e}")
        results['database'] = False

    try:
        results['audit_logging'] = test_audit_logging()
    except Exception as e:
        print(f"[FAIL] Audit logging error: {e}")
        results['audit_logging'] = False

    try:
        results['escalation_rules'] = test_escalation_rules()
    except Exception as e:
        print(f"[FAIL] Escalation rules error: {e}")
        results['escalation_rules'] = False

    try:
        results['cost_governance'] = test_cost_governance()
    except Exception as e:
        print(f"[FAIL] Cost governance error: {e}")
        results['cost_governance'] = False

    print("
" + "="*70)
    print("[SUMMARY] TEST RESULTS")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")

    print(f"
RESULTS: {passed}/{total} tests passed")
    print("="*70)

    if passed == total:
        print("[OK] ALL GOVERNANCE TESTS PASSED!")
        print("[OK] Intelsoft ARIA Governance Framework is OPERATIONAL")
        return True
    else:
        print("[FAIL] Some tests failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
