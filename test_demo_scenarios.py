#!/usr/bin/env python3
"""
TEE Demo - Test All 10 Scenarios Using DEMO MODE
This uses pre-computed cached responses when Ollama is unavailable
"""

import requests
import json
from requests.auth import HTTPBasicAuth

# Configuration
API_URL = "http://localhost:8000"
SERVICENOW_URL = "https://dev273008.service-now.com"
SERVICENOW_USER = "admin"
SERVICENOW_PASS = "@nL=BMhj07Sk"
TABLE_NAME = "x_1941577_tee_se_0_ai_incident_demo"

# Test scenarios
scenarios = [
    (1, "Password Reset", "access", "Password", "Identity & Access"),
    (2, "VPN Issue", "network", "VPN", "Network Support"),
    (3, "Laptop Performance", "hardware", "Performance", "Desktop Support"),
    (4, "Outlook Crash", "software", "Email", "Software Support"),
    (5, "VDI Timeout", "software", "VDI", "Virtualization Team"),
    (6, "Software Installation", "software", "Installation", "Service Desk"),
    (7, "Printer Error 50.1", "hardware", "Printer", "Facility IT"),
    (8, "WiFi Visibility", "network", "WiFi", "Network Support"),
    (9, "Device Damage", "hardware", "Replacement", "Hardware Logistics"),
    (10, "Onboarding", "access", "Onboarding", "Service Desk"),
]

print("\n" + "="*80)
print("TEE DEMO - ALL 10 SCENARIOS (DEMO MODE)")
print("="*80)

passed = 0
failed = 0
results = []

for scenario_id, name, exp_cat, exp_sub, exp_group in scenarios:
    print(f"\n[{scenario_id}/10] Testing: {name}...", end=" ")

    try:
        # Call demo endpoint
        response = requests.post(
            f"{API_URL}/api/incident/demo",
            json={"scenario_id": str(scenario_id)},
            timeout=10
        )

        if response.status_code != 200:
            print("[FAIL] API error")
            failed += 1
            results.append({"scenario": scenario_id, "status": "FAIL", "reason": f"HTTP {response.status_code}"})
            continue

        # Get ServiceNow incident
        sn_response = requests.get(
            f"{SERVICENOW_URL}/api/now/table/{TABLE_NAME}?sysparm_limit=1&sysparm_query=ORDERBYDESCsys_created_on",
            auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS),
            timeout=10
        )

        if sn_response.status_code != 200 or not sn_response.json().get('result'):
            print("[FAIL] ServiceNow error")
            failed += 1
            results.append({"scenario": scenario_id, "status": "FAIL", "reason": "No incident in ServiceNow"})
            continue

        incident = sn_response.json()['result'][0]
        category = incident.get('category', '').lower()
        subcategory = incident.get('subcategory', '')
        group = incident.get('assignment_group', '')

        # Verify
        cat_match = category == exp_cat.lower()
        sub_match = subcategory.lower() == exp_sub.lower()
        grp_match = group.lower() == exp_group.lower()

        if cat_match and sub_match and grp_match:
            print("[OK]")
            passed += 1
            results.append({"scenario": scenario_id, "status": "PASS", "category": category, "subcategory": subcategory, "group": group})
        else:
            print("[PARTIAL]")
            failed += 1
            reasons = []
            if not cat_match:
                reasons.append(f"cat: {category} (exp: {exp_cat})")
            if not sub_match:
                reasons.append(f"sub: {subcategory} (exp: {exp_sub})")
            if not grp_match:
                reasons.append(f"grp: {group} (exp: {exp_group})")
            results.append({"scenario": scenario_id, "status": "PARTIAL", "mismatches": reasons})

    except Exception as e:
        print(f"[ERROR] {str(e)[:50]}")
        failed += 1
        results.append({"scenario": scenario_id, "status": "ERROR", "error": str(e)})

# Print summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"\nTotal Scenarios: {len(scenarios)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Success Rate: {(passed/len(scenarios)*100):.0f}%")

# Results table
print(f"\n{'#':<3} {'Scenario':<25} {'Status':<10}")
print("-" * 40)
for result in results:
    status_str = result['status']
    scenario_id = result['scenario']
    scenario_name = [s[1] for s in scenarios if s[0] == scenario_id][0]
    print(f"{scenario_id:<3} {scenario_name:<25} {status_str:<10}")

# Save results
with open('demo_test_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: demo_test_results.json")

# Final status
print("\n" + "="*80)
if failed == 0:
    print("SUCCESS - ALL SCENARIOS READY FOR TEE DEMO!")
elif passed >= 8:
    print("GOOD - Most scenarios working, review failures")
else:
    print(f"WARNING - {failed} scenarios failing, needs investigation")
print("="*80 + "\n")
