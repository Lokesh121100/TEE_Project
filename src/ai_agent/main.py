from transformers import pipeline
import requests
from requests.auth import HTTPBasicAuth
import json
import os

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
    },
    {
        "description": "Outlook keeps crashing whenever I try to attach a PDF document. This is blocking my work.",
        "category": "Software",
        "subcategory": "Email",
        "caller": "alice.brown@company.com",
        "assignment_group": "Software Support"
    },
    {
        "description": "VDI session disconnects every 10 minutes. Getting a 'Session Timed Out' error repeatedly.",
        "category": "Software",
        "subcategory": "VDI",
        "caller": "charlie.davis@company.com",
        "assignment_group": "Virtualization Team"
    },
    {
        "description": "Need Adobe Acrobat Pro installed for a new project starting tomorrow. Manager has already approved.",
        "category": "Software",
        "subcategory": "Installation",
        "caller": "david.lee@company.com",
        "assignment_group": "Service Desk"
    },
    {
        "description": "Printer on Floor 3, Area B is offline. Paper jam cleared but screen still shows Error 50.1.",
        "category": "Hardware",
        "subcategory": "Printer",
        "caller": "emma.clark@company.com",
        "assignment_group": "Facility IT"
    },
    {
        "description": "Cannot see the 'Corporate_Guest' WiFi network on my mobile device. Other colleagues can connect fine.",
        "category": "Network",
        "subcategory": "WiFi",
        "caller": "frank.wright@company.com",
        "assignment_group": "Network Support"
    },
    {
        "description": "My current laptop has a cracked screen and the battery only lasts 20 minutes. Requesting a device replacement.",
        "category": "Hardware",
        "subcategory": "Replacement",
        "caller": "grace.hopper@company.com",
        "assignment_group": "Hardware Logistics"
    },
    {
        "description": "New joiner starting next Monday. Need to provision account, laptop, and building access badges.",
        "category": "Access",
        "subcategory": "Onboarding",
        "caller": "hr.admin@company.com",
        "assignment_group": "Identity & Access"
    }
]

# ==================== FUNCTIONS ====================

# ==================== RAG KNOWLEDGE BASE ====================
KB_PATH = "data/knowledge_base.json"

def retrieve_knowledge(user_description):
    """Simple Semantic Search (RAG Pattern)"""
    try:
        with open(KB_PATH, 'r') as f:
            kb = json.load(f)
        
        user_text = user_description.lower()
        best_match = None
        max_hits = 0
        
        for article in kb:
            hits = sum(1 for kw in article['keywords'] if kw in user_text)
            if hits > max_hits:
                max_hits = hits
                best_match = article
        
        if best_match:
            return f"[{best_match['id']}] {best_match['title']}: {best_match['steps']}"
        return "No specific KB article found. Routing to L2 for manual investigation."
    except Exception as e:
        return f"Retrieval Error: {str(e)}"

# ==================== RAG KNOWLEDGE BASE ====================
KB_PATH = "data/knowledge_base.json"

def retrieve_knowledge(user_description):
    """Simple Semantic Search (RAG Pattern)"""
    try:
        if not os.path.exists(KB_PATH):
            return "Knowledge Base file not found."
            
        with open(KB_PATH, 'r') as f:
            kb = json.load(f)
        
        user_text = user_description.lower()
        best_match = None
        max_hits = 0
        
        for article in kb:
            hits = sum(1 for kw in article['keywords'] if kw in user_text)
            if hits > max_hits:
                max_hits = hits
                best_match = article
        
        if best_match:
            return f"[{best_match['id']}] {best_match['title']}: {best_match['steps']}"
        return "No specific KB article found. Routing to L2 for manual investigation."
    except Exception as e:
        return f"Retrieval Error: {str(e)}"

# ==================== AUTOMATION ENGINE (Zero-Touch) ====================

def run_auto_resolution(subcategory, description):
    """Simulates automated diagnostics and self-healing"""
    print(f"  → AI Automation Engine triggered for [{subcategory}]...", end=" ")
    
    # Simulation logic for different automation scenarios
    if subcategory == "VPN":
        print("\n    [DIAGNOSTIC] Pinging VPN Server 'vpn.company.com'...", end=" ")
        print("FAIL (Timeout)")
        print("    [ACTION] Restarting 'GlobalProtect' Service and flushing DNS...", end=" ")
        return {
            "status": "Resolved", 
            "notes": "AI Auto-Resolution: VPN service was hung. Successfully restarted service and flushed DNS. Connectivity restored.",
            "success": True
        }
    
    elif subcategory == "Password":
        print("\n    [DIAGNOSTIC] Checking AD account status for user...", end=" ")
        print("LOCKED")
        print("    [ACTION] Triggering AD-Unlock-API and sending temporary MFA code...", end=" ")
        return {
            "status": "Resolved", 
            "notes": "AI Auto-Resolution: Account was locked. Triggered automated unlock and sent SMS code to verified mobile.",
            "success": True
        }
    
    elif subcategory == "VDI":
        print("\n    [DIAGNOSTIC] Checking VDI Session status for user...", end=" ")
        print("STUCK")
        print("    [ACTION] Resetting VDI session and clearing user profile cache...", end=" ")
        return {
            "status": "Resolved", 
            "notes": "AI Auto-Resolution: VDI session was stuck. Successfully reset session and cleared cache. User can now re-login.",
            "success": True
        }
    
    elif subcategory == "Replacement" or "cracked screen" in description.lower():
        print("\n    [DIAGNOSTIC] Analyzing device health logs...")
        print("    [SMART-LOCKER] Incident Linked. Assigning Secure Locker #402 for device collection.")
        return {
            "status": "New", # Keeps it New for the Tech Bar to physically fulfill
            "notes": "AI Automation: Hardware replacement triggered. Assigned Smart Locker #402. User has been notified with the collection PIN.",
            "success": True
        }
        
    else:
        print("No auto-fix available.")
        return {
            "status": "New", 
            "notes": "No automation trigger found for this subcategory. Assigned to L2 for manual handling.",
            "success": False
        }

def ollama_reasoning(prompt, model="llama3"):
    """Call local Ollama server for true AI reasoning"""
    try:
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get('response', '').strip()
    except Exception:
        return None
    return None

def generate_incident_summary(description):
    """Generate an AI summary using Ollama (Llama3)"""
    prompt = f"""You are an expert IT Service Desk analyst. 
Summarize the following user issue professionally for a ServiceNow incident in one sentence.
User Input: "{description}"
Output only the professional summary."""
    
    summary = ollama_reasoning(prompt)
    return summary if summary else f"Service Request: {description[:80]}"


def create_servicenow_incident(short_description, category, subcategory, caller, assignment_group, summary, knowledge, auto_fix):
    """Create an incident in ServiceNow with RAG and Automation context"""
    try:
        url = f"{SERVICENOW_URL}/api/now/table/{TABLE_NAME}"
        
        # Enhanced Payload with RAG Knowledge and Automation Notes
        payload = {
            "short_description": short_description,
            "category": category,
            "subcategory": subcategory,
            "caller": caller,
            "assignment_group": assignment_group,
            "status": auto_fix['status'],  # Dynamic status from Automation Engine
            "ai_confidence_score": 0.92,
            "ai_case_summary": summary,
            "ai_suggested_resolution": knowledge,
            "ai_automation_notes": auto_fix['notes'] # Detailed logs of what AI did
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

if __name__ == "__main__":
    print("=" * 60)
    print("TEE DEMO: AI-Powered ServiceNow Incident Creation")
print("=" * 60)

for i, scenario in enumerate(scenarios, 1):
    print(f"\n[Scenario {i}]")
    print(f"Description: {scenario['description'][:60]}...")
    
    # Step 1: Generate summary with AI
    print("  → AI Summary Generator...", end=" ")
    summary = generate_incident_summary(scenario['description'])
    print("Done!")
    
    # Step 2: RAG Retrieval
    print("  → RAG Knowledge Retrieval...", end=" ")
    knowledge = retrieve_knowledge(scenario['description'])
    print("Done!")
    
    # Step 3: Automation Engine (Check if we can fix it)
    auto_fix = run_auto_resolution(scenario['subcategory'], scenario['description'])
    print("Done!")
    
    # Step 4: Create incident in ServiceNow
    print("  → Creating incident in ServiceNow...", end=" ")
    success = create_servicenow_incident(
        short_description=summary,
        category=scenario['category'],
        subcategory=scenario['subcategory'],
        caller=scenario['caller'],
        assignment_group=scenario['assignment_group'],
        summary=summary,
        knowledge=knowledge,
        auto_fix=auto_fix
    )
    
    if not success:
        print("\n  ⚠ Failed to create incident. Check your ServiceNow credentials!")

print("\n" + "=" * 60)
print("Demo completed! Check your ServiceNow table for new incidents.")
print("=" * 60)