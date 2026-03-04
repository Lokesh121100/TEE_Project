import sys
import os
import time

sys.path.append(os.path.join(os.getcwd(), 'src', 'ai_agent'))

try:
    from main import (
        scenarios,
        generate_incident_summary_tuple,  # Use the tuple-returning version for the demo pipeline
        generate_aria_response,
        retrieve_knowledge,
        run_auto_resolution,
        create_servicenow_incident,
        SERVICENOW_URL
    )
except ImportError as e:
    print(f"Error: Could not import TEE core modules. Are you running from project root? {e}")
    sys.exit(1)

def run_demo():
    print("=" * 70)
    print("  TEE LIVE DEMO: AI-POWERED SERVICE DESK")
    print("=" * 70)
    print(f"Target Instance: {SERVICENOW_URL}")
    print(f"Total Scenarios: {len(scenarios)}")
    print("-" * 70)

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[SCENARIO {i}/{len(scenarios)}]: {scenario['category']} - {scenario['subcategory']}")
        print(f"   Required Tool: {scenario['tool']}")
        print(f"   Message: \"{scenario['description']}\"")
        print(f"   User:    {scenario['caller']}")
        
        print("\n   [AI ARIA DIALOGUE]")
        print("   ARIA is analyzing and responding...", end=" ", flush=True)
        aria_reply = generate_aria_response(scenario['description'], scenario_id=scenario['id'])
        print(f"DONE\n     ARIA: \"{aria_reply}\"")
        
        print("\n   [AI SUMMARIZATION]")
        print("   Generating professional ServiceNow summary...", end=" ", flush=True)
        title, analysis = generate_incident_summary_tuple(
            scenario['description'],
            category=scenario['category'],
            subcategory=scenario['subcategory'],
            caller=scenario['caller'],
            confidence=0.92
        )
        print(f"DONE\n     Title: \"{title}\"\n     Analysis: \"{analysis}\"")
        
        print("\n   [RAG KNOWLEDGE RETRIEVAL]")
        print("   Searching local 10-article KB...", end=" ", flush=True)
        knowledge = retrieve_knowledge(scenario['description'])
        print("DONE")
        print(f"     Match: {knowledge[:80]}...")
        
        print("\n   [AUTOMATION ENGINE]")
        auto_fix = run_auto_resolution(scenario['subcategory'], scenario['description'])
        print(f"     Result: {auto_fix['status']} - {auto_fix['notes'][:80]}...")
        
        print("\n   [SERVICENOW INTEGRATION]")
        print("   Transmitting to ServiceNow API...", end=" ", flush=True)
        success, inc_num = create_servicenow_incident(
            short_description=title,
            category=scenario['category'],
            subcategory=scenario['subcategory'],
            caller=scenario['caller'],
            assignment_group=scenario['assignment_group'],
            summary=analysis,
            knowledge=knowledge,
            auto_fix=auto_fix
        )
        
        if success:
            print(f"   SUCCESS: Ticket {inc_num} created.")
        else:
            print("   FAILED: Check logs.")

        print("\n" + "-" * 70)
        time.sleep(1)

    print("\n" + "=" * 70)
    print("  DEMO COMPLETED SUCCESSFULLY")
    print("    Check ServiceNow for the AI-Categorized and Routed Incidents.")
    print("=" * 70)

if __name__ == "__main__":
    run_demo()