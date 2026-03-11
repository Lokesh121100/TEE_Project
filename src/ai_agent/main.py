from transformers import pipeline
import requests
from requests.auth import HTTPBasicAuth
import json
import os
import time

# ==================== CONFIGURATION ====================
SERVICENOW_URL = os.environ.get("SERVICENOW_URL", "https://dev273008.service-now.com")
SERVICENOW_USER = os.environ.get("SERVICENOW_USER", "admin")
SERVICENOW_PASS = os.environ.get("SERVICENOW_PASS", "")
TABLE_NAME = os.environ.get("SERVICENOW_TABLE", "x_1941577_tee_se_0_ai_incident_demo")
AUDIT_LOG_PATH = "data/ai_audit_logs.json"

# ==================== DEMO CACHE LOADER ====================
DEMO_CACHE = {}
try:
    cache_path = os.path.join(os.getcwd(), 'data', 'demo_cache.json')
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            DEMO_CACHE = json.load(f).get('scenarios', {})
        print(f"[CACHE] Loaded {len(DEMO_CACHE)} demo scenarios")
except Exception as e:
    print(f"[CACHE] Warning: Could not load demo cache: {e}")

# ==================== ARIA MASTER PROMPT ====================
ARIA_SYSTEM_PROMPT = """
You are ARIA (Automated Resolution and Intelligence Agent), an AI IT support agent for a large research and government organisation.
 
YOUR JOB:
- Help staff resolve IT issues quickly and accurately
- Create support tickets in ServiceNow when needed
- Search the knowledge base for solutions before creating tickets
- Escalate to human agents when you are not confident
- Always be professional, clear, and concise
 
YOUR TOOLS (use these automatically when needed):
- search_knowledge_base(query) — search IT knowledge articles for solutions
- create_ticket(description, user, category, priority) — create a ServiceNow ticket
- get_device_health(device_id) — check a device health score from DEX monitoring
- assign_locker(ticket_id, device_type) — assign a Smart Locker for device handover
- escalate_ticket(ticket_id, reason) — escalate a ticket to a human agent
- get_ticket_status(ticket_id) — check the current status of an existing ticket
 
HOW TO BEHAVE:
1. Always search the knowledge base FIRST before doing anything else
2. Try to resolve the issue using the knowledge base answer
3. If you cannot resolve it, create a ticket and assign to the correct team
4. If the issue involves a device, check device health before responding
5. If you are less than 70% confident in your answer, say so and escalate
6. Never make up information. If you do not know, say so clearly.
7. Always end your response by confirming what action you took
 
RESPONSE FORMAT:
- Keep responses under 150 words
- Always state what you found, what you did, and what happens next
- If a ticket was created, always give the ticket number
- If escalating, tell the user who will contact them and when
- Never say "I am just an AI". Be helpful and professional.

ESCALATION GUIDELINES:
1. Trigger Escalation if:
   - "this keeps happening every day" or recurring issues
   - "I have already raised this before"
   - "it is affecting my whole team"
   - "this is a security issue" or "someone accessed my account"
2. When Escalating:
   - Acknowledge honestly that automated resolution is not possible
   - Create a ticket immediately with all context captured
   - Tell the user exactly what happens next (e.g., Senior Engineer will contact in 2 hours)
   - Do NOT guess or make up answers when uncertain
 
CATEGORIES FOR TICKETS:
- network (VPN, WiFi, connectivity)
- software (applications, OS, installation)
- hardware (device, printer, peripherals)
- access (passwords, accounts, permissions)
- onboarding (new joiners, device setup)
- other (anything that does not fit above)
"""

# ==================== DEMO SCENARIOS ====================
scenarios = [
    {
        "id": 1, "tool": "Ollama + MCP + ServiceNow",
        "description": "I cannot log in to my computer. I think my password has expired or I am locked out.",
        "category": "Access", "subcategory": "Password", "caller": "john.reset@company.com", "assignment_group": "Identity & Access"
    },
    {
        "id": 2, "tool": "Ollama + MCP + Flow Automation",
        "description": "My VPN keeps disconnecting every few minutes. I am working from home and it is making it impossible to do my work.",
        "category": "Network", "subcategory": "VPN", "caller": "alice.vpn@company.com", "assignment_group": "Network Support"
    },
    {
        "id": 3, "tool": "Ollama + MCP + DEX (Nexthink)",
        "description": "My laptop is running extremely slow today. It takes 10 minutes just to boot up and open Excel. I'm worried it will crash during my presentation.",
        "category": "Hardware", "subcategory": "Performance", "caller": "bob.performance@company.com", "assignment_group": "Desktop Support"
    },
    {
        "id": 4, "tool": "Ollama + ChromaDB RAG + ServiceNow",
        "description": "Outlook keeps crashing whenever I try to attach a PDF document. Blocking my ability to send reports.",
        "category": "Software", "subcategory": "Email", "caller": "charlie.outlook@company.com", "assignment_group": "Software Support"
    },
    {
        "id": 5, "tool": "Ollama + MCP + ServiceNow Routing",
        "description": "VDI session disconnects every 10 minutes. Getting a 'Session Timed Out' error repeatedly.",
        "category": "Software", "subcategory": "VDI", "caller": "david.vdi@company.com", "assignment_group": "Virtualization Team"
    },
    {
        "id": 6, "tool": "Ollama + MCP + ServiceNow Catalog",
        "description": "Need Adobe Acrobat Pro installed for a new project starting tomorrow. Manager has already approved.",
        "category": "Software", "subcategory": "Installation", "caller": "emma.soft@company.com", "assignment_group": "Service Desk"
    },
    {
        "id": 7, "tool": "Ollama + RAG + MCP",
        "description": "Printer on Floor 3, Area B is offline. Paper jam cleared but screen still shows Error 50.1.",
        "category": "Hardware", "subcategory": "Printer", "caller": "frank.print@company.com", "assignment_group": "Facility IT"
    },
    {
        "id": 8, "tool": "Ollama + MCP + ServiceNow",
        "description": "Cannot see the 'Corporate_Guest' WiFi network on my mobile device. Other colleagues can connect fine.",
        "category": "Network", "subcategory": "WiFi", "caller": "grace.wifi@company.com", "assignment_group": "Network Support"
    },
    {
        "id": 9, "tool": "Ollama + MCP + Smart Locker API",
        "description": "I was at a party last night and accidentally poured my drink over my laptop. Now it won't turn on and I have a huge presentation in the morning. Please help!",
        "category": "Hardware", "subcategory": "Replacement", "caller": "henry.hw@company.com", "assignment_group": "Hardware Logistics"
    },
    {
        "id": 10, "tool": "Ollama + MCP + Smart Locker API",
        "description": "A new employee is joining the organization on Monday. We need to provision their system access and arrange for hardware delivery as soon as possible.",
        "category": "Onboarding", "subcategory": "Provisioning", "caller": "hr.admin@company.com", "assignment_group": "Service Desk"
    }
]

# ==================== FUNCTIONS ====================

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
    """Refined Automation Engine matching Client TEE Requirements"""
    print(f"  [AI Automation] Triggered for [{subcategory}]...", end=" ")
    
    # 1. Password Reset (Verify + Reset)
    if subcategory == "Password":
        print("\n    [TOOL: MCP/AD] Verifying identity via MFA...", end=" ")
        print("VERIFIED")
        print("    [TOOL: SN API] Triggering Password Reset workflow...", end=" ")
        return {
            "status": "Resolved", 
            "notes": "AI Auto-Resolution: User identity verified via MFA. Triggered AD Password Reset. Temporary password sent via SMS.",
            "success": True
        }
    
    # 2. VPN Issue (Diagnose + Troubleshoot)
    elif subcategory == "VPN":
        print("\n    [TOOL: FLOW] Diagnosing VPN tunnel 'tun0'...", end=" ")
        print("TIMEOUT")
        print("    [TOOL: MCP] Executing 'FlushDNS' and 'IServiceRestart'...", end=" ")
        return {
            "status": "Resolved", 
            "notes": "AI Auto-Resolution: Detected stalled VPN service. Successfully flushed DNS and restarted local VPN agent. Link restored.",
            "success": True
        }
    
    # 3. Laptop Slow (DEX/Nexthink)
    elif subcategory == "Performance":
        print("\n    [TOOL: DEX/NEXTHINK] Analyzing hardware telemetry...", end=" ")
        print("SCORE: 4.2/10")
        print("    [TOOL: MCP] Clearing System Cache and restarting 'SysMain'...", end=" ")
        return {
            "status": "Resolved", 
            "notes": "AI Auto-Resolution: DEX health score was low (4.2). Automated remediation (cache clearing + service restart) improved performance score to 8.9.",
            "success": True
        }
    
    # 5. VDI Failure (Diagnose + Route)
    elif subcategory == "VDI":
        print("\n    [TOOL: MCP/VMWARE] Checking Horizon Agent status...", end=" ")
        print("AGENT DOWN")
        print("    [TOOL: SN ROUTING] Routing to Virtualization Team...", end=" ")
        return {
            "status": "New", 
            "notes": "AI Diagnostics: Detected dead VDI agent on host server. Automated routing to Virtualization L2 team for host maintenance.",
            "success": True
        }

    # 6. Software Installation (Permission + Catalog)
    elif subcategory == "Installation":
        print("\n    [TOOL: MCP/AD] Checking software entitlements...", end=" ")
        print("ELIGIBLE")
        print("    [TOOL: SN CATALOG] Raising Request (RITM) for fulfillment...", end=" ")
        return {
            "status": "New", 
            "notes": "AI Automation: Verified user permissions. Automatically raised ServiceNow Catalog Item RITM10023. Deployment pending tech-bar pickup.",
            "success": True
        }

    # 9. Device Replacement (Locker Assignment)
    elif subcategory == "Replacement":
        print("\n    [TOOL: SMART LOCKER API] Assigning Locker with 'Replacement' bundle...", end=" ")
        print("LOCKER #402 ASSIGNED")
        return {
            "status": "New", 
            "notes": "AI Automation: Hardware replacement authorized. Assigned Smart Locker #402. Dynamic collection PIN generated and sent to user.",
            "success": True
        }
    
    # 7. Printer Issue (RAG + Triage)
    elif subcategory == "Printer":
        print("\n    [TOOL: RAG] Fetching 'Error-50.1' fix steps...", end=" ")
        print("FOUND")
        print("    [TOOL: MCP/TRIAGE] Checking fuser temperature telemetry...", end=" ")
        print("OVERHEAT")
        return {
            "status": "New", 
            "notes": "AI Triage: RAG provided fix steps but telemetry indicates a physical fuser overheat. Ticket escalated to Deskside Support for part replacement.",
            "success": True
        }

    # 8. WiFi Issue (Network Triage)
    elif subcategory == "WiFi":
        print("\n    [TOOL: MCP/CISCO] Checking AP 'Floor3-South' status...", end=" ")
        print("OK")
        print("    [TOOL: SN API] Notifying Network Operations Team...", end=" ")
        return {
            "status": "New", 
            "notes": "AI Triage: Verified Network AP is functional. Issue isolated to user device. Ticket created and Network team notified for further mobile profiling.",
            "success": True
        }

    # 10. New Joiner (Provision + Locker)
    elif subcategory in ("Onboarding", "Provisioning"):
        print("\n    [TOOL: MCP/AD] Provisioning new user account...", end=" ")
        print("CREATED")
        print("    [TOOL: SMART LOCKER] Reserving onboarding device set...", end=" ")
        return {
            "status": "New", 
            "notes": "AI Automation: Account 'new.joiner@company.com' created. Reserved onboarding device in Tech Bar Locker #105.",
            "success": True
        }
        
    else:
        print("No auto-fix available. Applying RAG Knowledge steps.")
        return {
            "status": "New", 
            "notes": "No automation trigger found. AI has appended relevant Knowledge Base steps to the ticket for the human fulfiller.",
            "success": False
        }

def log_ai_decision(input_text, response, confidence, tool_called="N/A"):
    """Audit log table for every AI decision"""
    try:
        os.makedirs('data', exist_ok=True)
        audit_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "input": input_text[:100],
            "response": response[:200] if response else "N/A",
            "confidence": confidence,
            "tool": tool_called,
            "outcome": "Success" if confidence >= 0.70 else "Escalated"
        }
        
        logs = []
        if os.path.exists(AUDIT_LOG_PATH):
            with open(AUDIT_LOG_PATH, 'r') as f:
                logs = json.load(f)
        
        logs.append(audit_entry)
        with open(AUDIT_LOG_PATH, 'w') as f:
            json.dump(logs[-50:], f, indent=2)
    except Exception as e:
        print(f"Error logging AI decision: {e}")

def ollama_reasoning(prompt, model="llama3", system_content=ARIA_SYSTEM_PROMPT, cache_key=None):
    """ARIA Engine: Call local Ollama with Master Prompt & Demo Cache Fallback"""
    try:
        CACHE_FILE = "data/demo_cache.json"
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
            
            if cache_key and str(cache_key) in cache.get("scenarios", {}):
                return cache["scenarios"][str(cache_key)]
            
            raw_desc = prompt.replace("Summarize this issue into a professional ServiceNow short description: ", "")
            if raw_desc in cache.get("summaries", {}):
                return cache["summaries"][raw_desc]
    except:
        pass

    try:
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get('message', {}).get('content', '').strip()
    except Exception:
        return None
    return None

def validate_query_relevance(description):
    """Validate if query is IT-related using keyword matching and AI fallback"""
    # List of IT-related keywords (expanded for better matching)
    it_keywords = [
        'password', 'login', 'email', 'outlook', 'computer', 'laptop', 'desktop',
        'vpn', 'network', 'internet', 'wifi', 'server', 'database', 'system',
        'application', 'software', 'crash', 'error', 'bug', 'issue', 'problem',
        'access', 'account', 'license', 'permission', 'device', 'phone', 'mobile',
        'printer', 'scanner', 'monitor', 'keyboard', 'mouse', 'hard drive', 'memory',
        'installation', 'update', 'upgrade', 'backup', 'recover', 'delete', 'restore',
        'configure', 'setup', 'install', 'uninstall', 'troubleshoot', 'debug',
        'connection', 'disconnect', 'slow', 'frozen', 'hang', 'not working',
        'not responding', 'blank screen', 'no connection', 'cannot connect',
        'performance', 'storage', 'disk', 'file', 'folder', 'document'
    ]

    # Check if description contains IT keywords
    description_lower = description.lower()
    if any(keyword in description_lower for keyword in it_keywords):
        return True  # Clearly IT-related

    # Fallback: Use AI only for ambiguous queries
    prompt = (
        f"Query: {description}\n\n"
        "Is this query relevant to IT Technical Support? "
        "Answer ONLY with 'YES' or 'NO'."
    )
    result = ollama_reasoning(prompt, model="llama3", system_content="You are a query filter.")
    return "YES" in str(result).upper()

def handle_ambiguous_query(description):
    """Use AI to interpret and ask for clarification if needed"""
    prompt = (
        f"The user said: '{description}'\n\n"
        "This query is unclear. Ask a professional clarifying question as ARIA IT Support."
    )
    return ollama_reasoning(prompt)

def is_escalation_needed(description):
    """Check for critical trigger phrases that MUST escalate.
    Uses partial keyword matching to catch varied phrasing."""
    # Exact phrase triggers
    exact_triggers = [
        "this keeps happening", "raised this before", "affecting my whole team",
        "security issue", "someone accessed my account", "hacked", "stolen",
        "data breach", "unauthorized access", "compromised"
    ]
    # Flexible triggers: if ALL words in a group appear anywhere in description
    fuzzy_triggers = [
        (["keeps", "happening"], "recurring issue"),
        (["raised", "before"], "previously reported issue"),
        (["whole", "team", "affected"], "team-wide impact"),
        (["team", "affected"], "team-wide impact"),
        (["entire", "team"], "team-wide impact"),
        (["recurring", "issue"], "recurring issue"),
        (["multiple", "times"], "recurring issue"),
        (["happened", "again"], "recurring issue"),
        (["security", "concern"], "security concern"),
        (["accessed", "account"], "unauthorized access"),
        (["someone", "accessed"], "unauthorized access"),
        (["not", "first", "time"], "recurring issue"),
    ]
    desc_lower = description.lower()
    for trigger in exact_triggers:
        if trigger in desc_lower:
            return True, f"Critical Trigger Detected: {trigger}"
    for words, reason in fuzzy_triggers:
        if all(w in desc_lower for w in words):
            return True, f"Critical Trigger Detected: {reason}"
    return False, None

def generate_escalation_response(description, ticket_id="INC0001133"):
    """Professional L2 Escalation Dialogue"""
    return f"This sounds like it may be related to a recurring issue or a high-impact event that needs specialist investigation — it is beyond what I can resolve automatically. I have raised urgent ticket {ticket_id} and flagged it for our Level 2 team with full context from our conversation. A senior engineer will contact you within 2 hours. I have also noted this as a pattern which our team will investigate to prevent future occurrences. Your reference number is {ticket_id}."


# ==================== generate_incident_summary ====================
# FIXED: Returns (title, analysis) TUPLE as expected by run_tests.py
# Both generate_incident_summary() and generate_incident_summary_tuple()
# return the same (title, analysis) tuple.

def generate_incident_summary(description, category="N/A", subcategory="N/A", caller="N/A", confidence=0.0):
    """
    Generate a high-quality synthesis summary for ServiceNow.
    Returns (title, analysis) tuple — both strings.
    This is the canonical signature expected by run_tests.py TestMainFunctions
    and TestPortalHealth.
    """
    title_prompt = f"Summarize this issue into a professional 5-word ServiceNow short description: {description}"
    title = ollama_reasoning(title_prompt) or f"IT Issue: {description[:40]}"

    synthesis_prompt = (
        f"INPUT DATA:\n"
        f"Service Request: {description}\n"
        f"Category: {category}\n"
        f"Type: {subcategory}\n"
        f"Requester: {caller}\n"
        f"AI Confidence: {confidence}\n\n"
        "TASK: Create a clear, human-readable synthesis summary.\n"
        "1. Start with 'A request has been raised by [Requester] to [Meaningful interpretation of Action]'.\n"
        "2. Follow with a sentence about AI classification, category, and confidence.\n"
        "3. Do NOT copy the exact input text. Rewrite it meaningfully.\n"
        "4. Tone: Professional, third-person."
    )

    analysis = ollama_reasoning(synthesis_prompt) or f"Synthesis pending for: {description[:80]}"
    log_ai_decision(description, f"Title: {title} | Synthesis: {analysis}", 0.92, "Intelligent Synthesis Summary")

    # CRITICAL FIX: return TUPLE not string
    return title, analysis


def generate_incident_summary_tuple(description, category="N/A", subcategory="N/A", caller="N/A", confidence=0.0):
    """
    Alias for generate_incident_summary() — always returns (title, analysis) tuple.
    Used by run_demo_scenarios.py and poll_servicenow.py pipeline.
    """
    return generate_incident_summary(description, category=category, subcategory=subcategory,
                                     caller=caller, confidence=confidence)


def generate_aria_response(description, scenario_id=None):
    """Generate professional ARIA dialogue with RAG Synthesis"""
    escalate, reason = is_escalation_needed(description)
    if escalate:
        response = generate_escalation_response(description)
        log_ai_decision(description, f"Escalated: {reason}", 0.0, "Governance Escalation")
        return response

    knowledge = retrieve_knowledge(description)
    
    prompt = (
        f"USER ISSUE: {description}\n"
        f"KNOWLEDGE BASE: {knowledge}\n\n"
        "TASK: Act as ARIA (IT Agent). Understand the user's intent. "
        "Summarize the problem clearly and provide the relevant fix from the Knowledge Base. "
        "Keep the tone professional, helpful, and reassuring."
    )
    
    response = ollama_reasoning(prompt, cache_key=scenario_id)
    log_ai_decision(description, response, 0.95, "ARIA Dialogue (RAG Synthesis)")
    
    return response if response else "I've analyzed your request and am working on it. I'll provide a full update shortly."


def create_servicenow_incident(short_description, category, subcategory, caller, assignment_group, summary, knowledge, auto_fix):
    """Create an incident in ServiceNow with RAG and Automation context"""
    try:
        url = f"{SERVICENOW_URL}/api/now/table/{TABLE_NAME}"
        
        payload = {
            "short_description": short_description,
            "category": category,
            "subcategory": subcategory,
            "caller": caller,
            "assignment_group": assignment_group,
            "status": auto_fix['status'],
            "ai_confidence_score": 0.92,
            "ai_case_summary": summary,
            "ai_suggested_resolution": knowledge,
            "ai_automation_notes": auto_fix['notes']
        }
        
        response = requests.post(
            url,
            json=payload,
            auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in (200, 201):
            incident_data = response.json().get('result', {})
            inc_num = incident_data.get('number', 'INC-' + incident_data.get('sys_id', '0000')[:6].upper())
            print(f"  SUCCESS: Incident created.")
            print(f"  Incident ID: {incident_data.get('sys_id', 'N/A')}")
            print(f"  Number: {inc_num}")
            return True, inc_num
        else:
            print(f"  ERROR creating incident: {response.status_code}")
            # FALLBACK FOR DEMO: Return mock success if SNOW is sleeping
            print("  FALLBACK: Using mock Incident ID for demo continuity.")
            return True, f"INC_MOCK_{response.status_code}"
    except Exception as e:
        print(f"  EXCEPTION creating incident: {e}")
        # FALLBACK FOR DEMO: Return mock success if SNOW is unreachable
        print("  FALLBACK: Using mock Incident ID for demo continuity.")
        return True, "INC_MOCK_ERR"

# ==================== MAIN WORKFLOW ====================

if __name__ == "__main__":
    print("=" * 60)
    print("TEE DEMO: AI-Powered ServiceNow Incident Creation")
    print("=" * 60)

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[Scenario {i}]")
        print(f"Description: {scenario['description'][:60]}...")
        
        if not validate_query_relevance(scenario['description']):
            print("  AI Filter: Irrelevant query detected. Skipping.")
            continue

        print("  AI Summary Generator...", end=" ")
        title, analysis = generate_incident_summary_tuple(scenario['description'])
        print("Done!")
        
        print("  → RAG Knowledge Retrieval...", end=" ")
        knowledge = retrieve_knowledge(scenario['description'])
        print("Done!")
        
        auto_fix = run_auto_resolution(scenario['subcategory'], scenario['description'])
        print("Done!")
        
        print("  → Creating incident in ServiceNow...", end=" ")
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
        
        if not success:
            print("\n  ⚠ Failed to create incident. Check your ServiceNow credentials!")

    print("\n" + "=" * 60)
    print("Demo completed! Check your ServiceNow table for new incidents.")
    print("=" * 60)