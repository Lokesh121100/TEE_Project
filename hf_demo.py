from transformers import pipeline
import requests
from requests.auth import HTTPBasicAuth

# ==================== CONFIGURATION ====================
SERVICENOW_URL = "https://dev273008.service-now.com"
SERVICENOW_USER = "admin"
SERVICENOW_PASS = "@nL=BMhj07Sk"
TABLE_NAME = "x_1941577_tee_se_0_ai_incident_demo"

# ==================== DEMO SCENARIOS ====================
scenarios = [
    {
        "description": "User cannot connect to corporate VPN from home office. Restarted device but issue persists.",
        "category": "Network",
        "subcategory": "VPN",
        "caller": "john.doe@company.com",
        "assignment_group": "Network Support"
    },
    {
        "description": "User locked out of account after multiple failed login attempts. Needs immediate password reset.",
        "category": "Access",
        "subcategory": "Password",
        "caller": "jane.smith@company.com",
        "assignment_group": "Identity & Access"
    },
    {
        "description": "Laptop running extremely slow, taking 5 minutes to open applications. Performance degraded significantly.",
        "category": "Hardware",
        "subcategory": "Performance",
        "caller": "bob.wilson@company.com",
        "assignment_group": "Desktop Support"
    }
]

# ==================== FUNCTIONS ====================

def generate_incident_summary(description):
    """Generate an AI summary using Hugging Face"""
    try:
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        summary = summarizer(description, max_length=30, min_length=10, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"Error generating summary: {e}")
        return description[:50]

def create_servicenow_incident(short_description, category, subcategory, caller, assignment_group, summary):
    """Create an incident in ServiceNow"""
    try:
        url = f"{SERVICENOW_URL}/api/now/table/{TABLE_NAME}"
        
        payload = {
            "short_description": short_description,
            "category": category,
            "subcategory": subcategory,
            "caller": caller,
            "assignment_group": assignment_group,
            "status": "New",
            "ai_confidence_score": 0.92,
            "ai_case_summary": summary
        }
        
        response = requests.post(
            url,
            json=payload,
            auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            incident_data = response.json()['result']
            print(f"✓ Incident created successfully!")
            print(f"  Incident ID: {incident_data.get('sys_id', 'N/A')}")
            print(f"  Number: {incident_data.get('number', 'N/A')}")
            return True
        else:
            print(f"✗ Error creating incident: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Exception creating incident: {e}")
        return False

# ==================== MAIN WORKFLOW ====================

print("=" * 60)
print("TEE DEMO: AI-Powered ServiceNow Incident Creation")
print("=" * 60)

for i, scenario in enumerate(scenarios, 1):
    print(f"\n[Scenario {i}]")
    print(f"Description: {scenario['description'][:60]}...")
    
    # Step 1: Generate summary with AI
    print("  → Generating AI summary...", end=" ")
    summary = generate_incident_summary(scenario['description'])
    print("Done!")
    print(f"  Summary: {summary[:50]}...")
    
    # Step 2: Create incident in ServiceNow
    print("  → Creating incident in ServiceNow...", end=" ")
    success = create_servicenow_incident(
        short_description=summary,
        category=scenario['category'],
        subcategory=scenario['subcategory'],
        caller=scenario['caller'],
        assignment_group=scenario['assignment_group'],
        summary=summary
    )
    
    if not success:
        print("\n  ⚠ Failed to create incident. Check your ServiceNow credentials!")

print("\n" + "=" * 60)
print("Demo completed! Check your ServiceNow table for new incidents.")
print("=" * 60)