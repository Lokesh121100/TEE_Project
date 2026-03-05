#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEE Demo - Test All 10 Scenarios in ServiceNow
This script tests all 10 demo scenarios to verify:
1. API processes them correctly
2. ServiceNow incidents are created
3. All fields are populated
4. Categorization is correct
"""

import requests
import json
import time
import sys
from requests.auth import HTTPBasicAuth
from datetime import datetime

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
API_URL = "http://localhost:8000"
SERVICENOW_URL = "https://dev273008.service-now.com"
SERVICENOW_USER = "admin"
SERVICENOW_PASS = "@nL=BMhj07Sk"
TABLE_NAME = "x_1941577_tee_se_0_ai_incident_demo"

# Test Scenarios
SCENARIOS = [
    {
        "id": 1,
        "name": "Password Reset",
        "description": "I forgot my password and cannot login to my computer. I need to reset it immediately.",
        "expected_category": "access",
        "expected_subcategory": "Password",
        "expected_group": "Identity & Access",
        "should_auto_resolve": True
    },
    {
        "id": 2,
        "name": "VPN Issue",
        "description": "My VPN keeps disconnecting every few minutes while I'm working from home. It's making it impossible to do my work.",
        "expected_category": "network",
        "expected_subcategory": "VPN",
        "expected_group": "Network Support",
        "should_auto_resolve": True
    },
    {
        "id": 3,
        "name": "Laptop Performance",
        "description": "My laptop is running extremely slow and takes 10 minutes to boot. I can't get my work done.",
        "expected_category": "hardware",
        "expected_subcategory": "Performance",
        "expected_group": "Desktop Support",
        "should_auto_resolve": False
    },
    {
        "id": 4,
        "name": "Outlook Crash",
        "description": "Outlook crashes when I try to attach a PDF document. This is blocking my work.",
        "expected_category": "software",
        "expected_subcategory": "Email",
        "expected_group": "Software Support",
        "should_auto_resolve": False
    },
    {
        "id": 5,
        "name": "VDI Timeout",
        "description": "My Horizon VDI session keeps timing out and disconnecting. I've restarted it 3 times this morning.",
        "expected_category": "software",
        "expected_subcategory": "VDI",
        "expected_group": "Virtualization Team",
        "should_auto_resolve": False
    },
    {
        "id": 6,
        "name": "Software Installation",
        "description": "I need Adobe Creative Suite installed on my laptop. How do I request this?",
        "expected_category": "software",
        "expected_subcategory": "Installation",
        "expected_group": "Service Desk",
        "should_auto_resolve": False
    },
    {
        "id": 7,
        "name": "Printer Error 50.1",
        "description": "My printer is showing Error 50.1 and won't print.",
        "expected_category": "hardware",
        "expected_subcategory": "Printer",
        "expected_group": "Facility IT",
        "should_auto_resolve": True
    },
    {
        "id": 8,
        "name": "WiFi Visibility",
        "description": "I can't see the corporate WiFi network on my laptop. Other networks are visible.",
        "expected_category": "network",
        "expected_subcategory": "WiFi",
        "expected_group": "Network Support",
        "should_auto_resolve": False
    },
    {
        "id": 9,
        "name": "Device Damage",
        "description": "I dropped my laptop and cracked the screen. It's still on but has a large crack. Can I get a replacement?",
        "expected_category": "hardware",
        "expected_subcategory": "Replacement",
        "expected_group": "Hardware Logistics",
        "should_auto_resolve": False
    },
    {
        "id": 10,
        "name": "New Joiner Onboarding",
        "description": "Hi, I'm starting today. I don't have a laptop yet or an Active Directory account. What do I need to do?",
        "expected_category": "access",
        "expected_subcategory": "Onboarding",
        "expected_group": "Service Desk",
        "should_auto_resolve": False
    }
]

# Test Results
results = {
    "total": len(SCENARIOS),
    "passed": 0,
    "failed": 0,
    "partial": 0,
    "scenarios": []
}

def test_scenario(scenario):
    """Test a single scenario"""
    print(f"\n{'='*80}")
    print(f"SCENARIO {scenario['id']}: {scenario['name']}")
    print(f"{'='*80}")

    test_result = {
        "id": scenario['id'],
        "name": scenario['name'],
        "api_response": None,
        "servicenow_incident": None,
        "status": "PENDING",
        "errors": [],
        "verification": {}
    }

    try:
        # Step 1: Call API
        print(f"\n[1/3] Calling API...")
        print(f"Description: {scenario['description'][:60]}...")

        response = requests.post(
            f"{API_URL}/api/incident",
            json={"description": scenario['description']},
            timeout=30
        )

        if response.status_code != 200:
            test_result['errors'].append(f"API returned {response.status_code}")
            print(f"[FAIL] API Error: {response.status_code}")
            return test_result

        api_data = response.json()
        test_result['api_response'] = api_data
        print(f"[OK] API Response: {str(api_data)[:100]}...")

        # Step 2: Check ServiceNow for recent incidents
        print(f"\n[2/3] Checking ServiceNow for incidents...")
        time.sleep(2)  # Wait for ServiceNow to process

        sn_response = requests.get(
            f"{SERVICENOW_URL}/api/now/table/{TABLE_NAME}?sysparm_limit=5&sysparm_query=ORDERBYDESCsys_created_on",
            auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS),
            timeout=10
        )

        if sn_response.status_code != 200:
            test_result['errors'].append(f"ServiceNow returned {sn_response.status_code}")
            print(f"[FAIL] ServiceNow Error: {sn_response.status_code}")
            return test_result

        sn_data = sn_response.json()
        incidents = sn_data.get('result', [])

        if not incidents:
            test_result['errors'].append("No incidents found in ServiceNow")
            print(f"[FAIL] No incidents found")
            return test_result

        # Find matching incident (most recent)
        latest_incident = incidents[0]
        test_result['servicenow_incident'] = latest_incident
        print(f"[OK] Found Incident in ServiceNow")
        print(f"   Sys ID: {latest_incident.get('sys_id', 'N/A')}")

        # Step 3: Verify incident details
        print(f"\n[3/3] Verifying incident details...")

        verification = {
            "short_description": latest_incident.get('short_description', ''),
            "category": latest_incident.get('category', ''),
            "subcategory": latest_incident.get('subcategory', ''),
            "assignment_group": latest_incident.get('assignment_group', ''),
            "status": latest_incident.get('status', ''),
            "confidence": latest_incident.get('ai_confidence_score', ''),
            "ai_summary": latest_incident.get('ai_case_summary', '')[:50] if latest_incident.get('ai_case_summary') else ''
        }

        test_result['verification'] = verification

        # Check expectations
        checks = {
            "category_match": verification['category'].lower() == scenario['expected_category'].lower(),
            "subcategory_match": verification['subcategory'].lower() == scenario['expected_subcategory'].lower(),
            "group_match": verification['assignment_group'].lower() == scenario['expected_group'].lower(),
            "has_confidence": bool(verification['confidence']),
            "has_summary": bool(verification['ai_summary']),
            "has_status": bool(verification['status'])
        }

        test_result['verification']['checks'] = checks

        # Print verification results
        print(f"   Category: {verification['category']} (Expected: {scenario['expected_category']}) {'[OK]' if checks['category_match'] else '[FAIL]'}")
        print(f"   Subcategory: {verification['subcategory']} (Expected: {scenario['expected_subcategory']}) {'[OK]' if checks['subcategory_match'] else '[FAIL]'}")
        print(f"   Group: {verification['assignment_group']} (Expected: {scenario['expected_group']}) {'[OK]' if checks['group_match'] else '[FAIL]'}")
        print(f"   Confidence: {verification['confidence']} {'[OK]' if checks['has_confidence'] else '[FAIL]'}")
        print(f"   Summary: {verification['ai_summary']}... {'[OK]' if checks['has_summary'] else '[FAIL]'}")
        print(f"   Status: {verification['status']} {'[OK]' if checks['has_status'] else '[FAIL]'}")

        # Determine overall status
        all_passed = all(checks.values())
        if all_passed:
            test_result['status'] = "PASSED"
            results['passed'] += 1
            print(f"\n[OK] SCENARIO PASSED")
        else:
            test_result['status'] = "PARTIAL"
            results['partial'] += 1
            print(f"\n[WARN] SCENARIO PARTIAL (some checks failed)")

        return test_result

    except Exception as e:
        test_result['errors'].append(str(e))
        test_result['status'] = "FAILED"
        results['failed'] += 1
        print(f"[FAIL] ERROR: {e}")
        return test_result

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("TEE DEMO - ALL 10 SCENARIOS TEST")
    print("="*80)
    print(f"\nStarting time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total scenarios: {len(SCENARIOS)}")
    print(f"API: {API_URL}")
    print(f"ServiceNow: {SERVICENOW_URL}")

    # Run all tests
    for scenario in SCENARIOS:
        result = test_scenario(scenario)
        results['scenarios'].append(result)
        time.sleep(1)  # Small delay between tests

    # Print Summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"\nTotal Scenarios: {results['total']}")
    print(f"[OK] Passed: {results['passed']}")
    print(f"[WARN] Partial: {results['partial']}")
    print(f"[FAIL] Failed: {results['failed']}")
    print(f"Success Rate: {(results['passed'] / results['total'] * 100):.1f}%")

    # Detailed results table
    print(f"\n\n{'#':<3} {'Scenario':<25} {'Status':<10} {'Category':<15} {'Group':<20}")
    print("-" * 73)
    for result in results['scenarios']:
        scenario_name = result['name']
        status = result['status']
        category = result['verification'].get('category', 'N/A')
        group = result['verification'].get('assignment_group', 'N/A')
        print(f"{result['id']:<3} {scenario_name:<25} {status:<10} {category:<15} {group:<20}")

    # Failed scenarios details
    failed_scenarios = [r for r in results['scenarios'] if r['status'] in ['FAILED', 'PARTIAL']]
    if failed_scenarios:
        print(f"\n\n[WARN] SCENARIOS WITH ISSUES ({len(failed_scenarios)}):")
        for result in failed_scenarios:
            print(f"\n  Scenario {result['id']}: {result['name']}")
            if result['errors']:
                for error in result['errors']:
                    print(f"    - {error}")
            if result['verification'].get('checks'):
                for check, passed in result['verification']['checks'].items():
                    if not passed:
                        print(f"    - {check}: FAILED")

    # Save detailed report
    report_file = "test_results.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n\nDetailed results saved to: {report_file}")

    # Final status
    print("\n" + "="*80)
    if results['failed'] == 0:
        if results['partial'] == 0:
            print("[OK] ALL TESTS PASSED - READY FOR TEE DEMO")
        else:
            print(f"[WARN] TESTS PASSED WITH {results['partial']} PARTIAL - CHECK DETAILS")
    else:
        print(f"[FAIL] {results['failed']} TESTS FAILED - NEEDS FIXING")
    print("="*80)

if __name__ == "__main__":
    main()
