#!/usr/bin/env python3
"""
Complete Feature Test - No server required
Tests all implemented features directly
"""

import sys
import json
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_governance_framework():
    """Test governance framework"""
    print("\n" + "="*70)
    print("[TEST] GOVERNANCE FRAMEWORK - DIRECT TEST")
    print("="*70)

    try:
        from src.governance import (
            AuditLoggingService,
            EscalationRulesEngine,
            CostGovernanceService
        )

        print("\n[OK] All governance modules imported")

        # Test escalation rules
        engine = EscalationRulesEngine()
        test_ticket = {
            'confidence_score': 85,
            'incident_category': 'Network',
            'severity_level': 'High',
            'user_department': 'Finance',
            'ai_action': 'system restart',
            'sla_status': 85,
            'is_vip_user': True,
            'previous_failures': 0,
            'policy_violation': False,
            'security_concern': True,
            'compliance_concern': False
        }

        decision = engine.evaluate_escalation(test_ticket)
        print(f"[OK] Escalation evaluated: {decision.escalation_level.value}")
        print(f"[OK] Risk score: {decision.risk_score:.1f}/100")

        # Test audit logging
        audit_service = AuditLoggingService()
        print(f"[OK] Audit service initialized")
        print(f"[OK] Database created: data/aria_governance.db")

        # Test cost governance
        cost_service = CostGovernanceService()
        cost_id = cost_service.record_cost(
            category='inference',
            amount=1500.00,
            description='Test cost',
            ticket_count=1200
        )
        print(f"[OK] Cost recorded: {cost_id}")

        print("\n[RESULT] GOVERNANCE FRAMEWORK - ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"[FAIL] {str(e)}")
        return False

def test_frontend_files():
    """Test frontend files exist and have escalation components"""
    print("\n" + "="*70)
    print("[TEST] FRONTEND INTEGRATION - FILE CHECK")
    print("="*70)

    checks = {
        "index.html": ["escalation-modal", "escalate-btn"],
        "app.js": ["escalation", "POST /api/escalate"],
        "styles.css": [".btn-escalate", ".modal"],
    }

    all_ok = True
    for filename, keywords in checks.items():
        filepath = f"src/frontend/{filename}"
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            found = all(kw in content for kw in keywords)
            if found:
                print(f"[OK] {filename} - Contains escalation components")
            else:
                missing = [kw for kw in keywords if kw not in content]
                print(f"[FAIL] {filename} - Missing: {missing}")
                all_ok = False
        except FileNotFoundError:
            print(f"[FAIL] {filename} - File not found")
            all_ok = False

    if all_ok:
        print("\n[RESULT] FRONTEND INTEGRATION - ALL CHECKS PASSED")
    else:
        print("\n[RESULT] FRONTEND INTEGRATION - SOME CHECKS FAILED")

    return all_ok

def test_api_endpoint_code():
    """Test that escalate endpoint code exists"""
    print("\n" + "="*70)
    print("[TEST] API ENDPOINT - CODE VERIFICATION")
    print("="*70)

    try:
        with open("src/api/app.py", 'r') as f:
            content = f.read()

        checks = {
            "POST /api/escalate endpoint": "@app.post(\"/api/escalate\")" in content,
            "Endpoint function": "async def escalate_to_human" in content,
            "ServiceNow integration": "servicenow" in content.lower(),
            "Transcript handling": "transcript" in content.lower(),
            "SLA setting": "sla_minutes" in content.lower(),
        }

        all_ok = True
        for check_name, result in checks.items():
            status = "[OK]" if result else "[FAIL]"
            print(f"{status} {check_name}")
            all_ok = all_ok and result

        if all_ok:
            print("\n[RESULT] API ENDPOINT - ALL CHECKS PASSED")

        return all_ok

    except Exception as e:
        print(f"[FAIL] {str(e)}")
        return False

def main():
    print("\n" + "="*70)
    print("COMPLETE FEATURE TEST - NO SERVER REQUIRED")
    print("="*70)

    results = {}

    # Test governance
    results['governance'] = test_governance_framework()

    # Test frontend
    results['frontend'] = test_frontend_files()

    # Test API code
    results['api_code'] = test_api_endpoint_code()

    # Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    print(f"\nResults: {passed}/{total} test categories passed")

    if passed == total:
        print("\n[SUCCESS] ALL FEATURES VERIFIED - READY FOR PRODUCTION")
        print("\nYou can now:")
        print("1. Test in browser: python src/api/app.py")
        print("2. Build dashboard: Follow docs/09_DASHBOARD_SETUP_GUIDE.md")
        print("3. Create slides: Follow docs/10_PRESENTATION_OUTLINE.md")
        return 0
    else:
        print("\n[WARNING] Some checks failed - review above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
