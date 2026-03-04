import requests
from requests.auth import HTTPBasicAuth
import json
import time

# Import the AI functions from main.py
from main import generate_incident_summary, retrieve_knowledge, run_auto_resolution, SERVICENOW_URL, SERVICENOW_USER, SERVICENOW_PASS, TABLE_NAME, ollama_reasoning

def intelligent_classification(description):
    """ARIA Engine: Intelligently classify and score confidence"""
    prompt = f"""
    Analyze this IT issue and provide routing metadata.
    Issue: "{description}"
    
    Category must be: [access, software, hardware, network, onboarding, other]
    Subcategory: specific (e.g., Password, VPN, Printer)
    Group: technical team (e.g., Service Desk, Network Support)
    Confidence: 0.0 to 1.0 (float)
    
    Output strictly in JSON format: {{"category": "...", "subcategory": "...", "group": "...", "confidence": 0.95}}
    """
    import re
    from main import log_ai_decision
    try:
        response_text = ollama_reasoning(prompt)
        if response_text:
            match = re.search(r'\{[^{}]+\}', response_text, re.DOTALL)
            if match:
                result = json.loads(match.group(0))
                cat = result.get('category', 'other')
                sub = result.get('subcategory', 'General')
                grp = result.get('group', 'Service Desk')
                conf = float(result.get('confidence', 0.5))
                
                # Governance: Log decision
                log_ai_decision(description, f"Classified as {cat}/{sub}", conf, "Classification")
                
                return cat, sub, grp, conf
    except Exception:
        pass
    return "other", "General", "Service Desk", 0.0

def classify_ticket(description):
    """Classify with Human-in-the-Loop guard (70% threshold + Trigger Keywords)"""
    from main import is_escalation_needed
    
    # 1. Check for Forced Escalation Triggers
    escalate, reason = is_escalation_needed(description)
    if escalate:
        print(f"    ⚠️ [GOVERNANCE] Forced Escalation: {reason}")
        # Force low confidence and route to Senior Support
        return "other", "Escalation", "L2 Senior Support", 0.0
        
    # 2. Proceed with AI Classification
    cat, sub, grp, conf = intelligent_classification(description)
    
    # Weak Spot 2: Confidence Threshold
    if conf < 0.70:
        print(f"    ⚠️ [GOVERNANCE] Low confidence ({conf:.2f}). Escalating to Human L2.")
        return cat, sub, "L2 Senior Support", conf
        
    return cat, sub, grp, conf


def poll_for_new_tickets():
    """Polls ServiceNow for tickets that haven't been analyzed by AI yet"""
    # Fetch both short_description and description
    url = f"{SERVICENOW_URL}/api/now/table/{TABLE_NAME}?sysparm_query=ai_case_summaryISEMPTY^ORai_case_summaryLIKEN/A&sysparm_limit=5&sysparm_fields=sys_id,number,short_description,description,status"
    
    try:
        response = requests.get(url, auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS))
        if response.status_code == 200:
            return response.json().get('result', [])
        return []
    except Exception as e:
        print(f"[ERROR] Failed to poll ServiceNow: {e}")
        return []

def update_ticket(sys_id, payload):
    """Updates the ticket in ServiceNow with AI Analysis"""
    url = f"{SERVICENOW_URL}/api/now/table/{TABLE_NAME}/{sys_id}"
    try:
        response = requests.put(
            url,
            json=payload,
            auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS),
            headers={"Content-Type": "application/json"}
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Failed to update ticket: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🛡️ AI Command Center: Live Polling Service Started")
    print("Listening for new manual tickets in ServiceNow...")
    print("Tip: Use the 'Description' field for long text (>40 chars)!")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    try:
        while True:
            tickets = poll_for_new_tickets()
            
            for ticket in tickets:
                sys_id = ticket.get('sys_id')
                desc = ticket.get('short_description', '')
                long_desc = ticket.get('description', '')
                number = ticket.get('number', 'UNKNOWN')
                
                # Prioritize the full description for AI engine, fallback to desc
                full_user_input = long_desc if long_desc and len(long_desc) > 5 else desc
                
                if not full_user_input or full_user_input == 'N/A':
                    continue
                    
                print(f"\n[!] New Manual Ticket Detected: {number}")
                print(f"    Short Title: '{desc}'")
                print(f"    Full Input Details: '{full_user_input[:80]}...'")
                
                # 1. AI Routing Classifier
                category, subcategory, group, confidence = classify_ticket(full_user_input)
                print(f"    [AI ROUTING] Assigned to {group} ({category} > {subcategory}) [Confidence: {confidence:.2f}]")
                
                # 2. AI Summarization
                print("    [AI ENGINE] Generating professional summary...")
                summary = generate_incident_summary(full_user_input)
                
                # 3. RAG Retrieval
                print("    [AI RAG] Searching Knowledge Base...")
                knowledge = retrieve_knowledge(full_user_input)
                
                # 4. Automation Engine
                auto_fix = run_auto_resolution(subcategory, full_user_input)
                
                # 5. Update ServiceNow
                if ticket.get('status') != 'Resolved':  # Don't downgrade status if empty
                    final_status = auto_fix['status']
                else:
                    final_status = ticket.get('status')
                    
                payload = {
                    "short_description": f"[AI PROCESSED] {desc}",
                    "category": category,
                    "subcategory": subcategory,
                    "assignment_group": group,
                    "ai_case_summary": summary,
                    "ai_suggested_resolution": knowledge,
                    "ai_automation_notes": auto_fix['notes'],
                    "ai_confidence_score": 0.94,
                    "status": final_status
                }
                
                print("    [SERVICENOW] Updating record with AI Analysis...")
                if update_ticket(sys_id, payload):
                    print(f"    ✅ Successfully processed: {desc[:30]}...")
                    print(f"       -> Record ID: {sys_id}")
                    print(f"       -> Automation: {auto_fix['notes'][:50]}...")
                else:
                    print(f"    ❌ Failed to update {number}.")

                    
            time.sleep(5) # Poll every 5 seconds
            
    except KeyboardInterrupt:
        print("\n[!] Polling service stopped.")
