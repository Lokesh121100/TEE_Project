import requests
from requests.auth import HTTPBasicAuth
import json
import re
import time

from main import (
    generate_incident_summary_tuple,
    retrieve_knowledge,
    run_auto_resolution,
    is_escalation_needed,
    SERVICENOW_URL,
    SERVICENOW_USER,
    SERVICENOW_PASS,
    TABLE_NAME,
    ollama_reasoning,
    log_ai_decision
)


# ==================== KEYWORD FALLBACK CLASSIFIER ====================
# Used when Ollama returns unparseable JSON or zero confidence.
# Ensures deterministic routing without needing the LLM.

_KEYWORD_RULES = [
    # (keywords_any_of, category, subcategory, group)
    (["vpn", "global protect", "globalprotect", "remote access", "tunnel"],
     "network", "VPN", "Network Support"),
    (["wifi", "wi-fi", "wireless", "ssid", "corporate_guest", "guest wifi"],
     "network", "WiFi", "Network Support"),
    (["vdi", "virtual desktop", "horizon", "citrix", "remote desktop", "session timed"],
     "network", "VDI", "Virtualization Team"),
    (["password", "locked", "lock out", "lockout", "credentials", "reset", "expired", "cannot log in", "can't log in", "login"],
     "access", "Password", "Identity & Access"),
    (["onboard", "new joiner", "new employee", "new staff", "start date", "provisioning", "provision"],
     "access", "Onboarding", "Service Desk"),
    (["sharepoint", "sap", "mfa", "authenticator", "permission", "access request"],
     "access", "Access Request", "Identity & Access"),
    (["outlook", "email", "mail", "attachment", "smtp"],
     "software", "Email", "Software Support"),
    (["install", "adobe", "acrobat", "chrome", "software request", "application"],
     "software", "Installation", "Service Desk"),
    (["teams", "microsoft teams", "freeze", "crash", "excel", "word", "office"],
     "software", "Application", "Software Support"),
    (["slow", "performance", "cpu", "ram", "boot", "startup", "freezing", "hang"],
     "hardware", "Performance", "Desktop Support"),
    (["printer", "print", "fuser", "paper jam", "scanner", "50.1"],
     "hardware", "Printer", "Facility IT"),
    (["crack", "screen", "liquid", "water", "spill", "broken", "replacement", "replace", "new device", "hinge"],
     "hardware", "Replacement", "Hardware Logistics"),
    (["laptop", "device", "keyboard", "battery", "hardware"],
     "hardware", "Hardware", "Desktop Support"),
]


def _keyword_classify(description: str):
    """Deterministic keyword-based fallback classification."""
    text = description.lower()
    for keywords, cat, sub, grp in _KEYWORD_RULES:
        if any(kw in text for kw in keywords):
            return cat, sub, grp, 0.85   # Assign a solid fallback confidence
    return "other", "General", "Service Desk", 0.75


def intelligent_classification(description):
    """
    ARIA Engine: Classify via Ollama LLM with robust JSON parsing.
    Falls back to keyword rules if Ollama returns unparseable output.
    """
    prompt = f"""Analyze this IT support issue and classify it.

Issue: "{description}"

Return ONLY a JSON object with these exact keys (no explanation, no markdown):
{{"category": "network", "subcategory": "VPN", "group": "Network Support", "confidence": 0.95}}

Category must be one of: access, software, hardware, network, onboarding, other
"""
    try:
        response_text = ollama_reasoning(prompt)
        if response_text:
            # Strip markdown code fences if present
            cleaned = re.sub(r"```(?:json)?", "", response_text).strip()

            # Try to extract a JSON object from anywhere in the response
            match = re.search(r'\{[^{}]+\}', cleaned, re.DOTALL)
            if match:
                result = json.loads(match.group(0))
                cat  = str(result.get('category', '')).strip().lower()
                sub  = str(result.get('subcategory', 'General')).strip()
                grp  = str(result.get('group', 'Service Desk')).strip()
                conf = float(result.get('confidence', 0.0))

                # Validate category is one of the allowed values
                allowed = {"access", "software", "hardware", "network", "onboarding", "other"}
                if cat not in allowed:
                    cat = "other"

                # If confidence is suspiciously low but category looks valid,
                # boost it so governance doesn't blindly escalate everything.
                if conf < 0.70 and cat != "other":
                    conf = 0.80

                log_ai_decision(description, f"Classified as {cat}/{sub}", conf, "Classification")
                return cat, sub, grp, conf

    except Exception:
        pass  # Fall through to keyword fallback

    # ── Keyword fallback ──────────────────────────────────────────
    cat, sub, grp, conf = _keyword_classify(description)
    log_ai_decision(description, f"Keyword fallback: {cat}/{sub}", conf, "Classification-Fallback")
    return cat, sub, grp, conf


def classify_ticket(description):
    """
    4-value public interface — used by run_tests.py accuracy suite.
    Returns (category, subcategory, group, confidence).

    Governance rules applied:
      - Forced escalation on critical trigger phrases
      - Low-confidence (<0.70) results routed to L2 Senior Support
    """
    # is_escalation_needed imported at module level — always available
    escalate, reason = is_escalation_needed(description)
    if escalate:
        print(f"    ⚠️ [GOVERNANCE] Forced Escalation: {reason}")
        return "other", "Escalation", "L2 Senior Support", 0.0

    cat, sub, grp, conf = intelligent_classification(description)

    if conf < 0.70:
        print(f"    ⚠️ [GOVERNANCE] Low confidence ({conf:.2f}). Escalating to Human L2.")
        return cat, sub, "L2 Senior Support", conf

    return cat, sub, grp, conf


def classify_ticket_full(description):
    """
    Full classification returning (category, subcategory, group, confidence).
    Used internally by portal and polling loop.
    Identical to classify_ticket — kept as alias for portal.py compatibility.
    """
    return classify_ticket(description)


def poll_for_new_tickets():
    """Polls ServiceNow for tickets that haven't been analyzed by AI yet."""
    url = (
        f"{SERVICENOW_URL}/api/now/table/{TABLE_NAME}"
        f"?sysparm_query=ai_case_summaryISEMPTY^ORai_case_summaryLIKEN/A"
        f"&sysparm_limit=5"
        f"&sysparm_fields=sys_id,number,short_description,description,status"
    )
    try:
        response = requests.get(url, auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS))
        if response.status_code == 200:
            return response.json().get('result', [])
        return []
    except Exception as e:
        print(f"[ERROR] Failed to poll ServiceNow: {e}")
        return []


def update_ticket(sys_id, payload):
    """Updates the ticket in ServiceNow with AI Analysis."""
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
                sys_id       = ticket.get('sys_id')
                desc         = ticket.get('short_description', '')
                long_desc    = ticket.get('description', '')
                number       = ticket.get('number', 'UNKNOWN')

                full_user_input = long_desc if long_desc and len(long_desc) > 5 else desc

                if not full_user_input or full_user_input == 'N/A':
                    continue

                print(f"\n[!] New Manual Ticket Detected: {number}")
                print(f"    Short Title: '{desc}'")
                print(f"    Full Input:  '{full_user_input[:80]}...'")

                category, subcategory, group, confidence = classify_ticket_full(full_user_input)
                print(f"    [AI ROUTING] → {group} ({category} > {subcategory}) [Conf: {confidence:.2f}]")

                print("    [AI ENGINE] Generating professional summary...")
                title, summary = generate_incident_summary_tuple(full_user_input)

                print("    [AI RAG] Searching Knowledge Base...")
                knowledge = retrieve_knowledge(full_user_input)

                auto_fix = run_auto_resolution(subcategory, full_user_input)

                final_status = auto_fix['status'] if ticket.get('status') != 'Resolved' else ticket.get('status')

                payload = {
                    "short_description":    f"[AI PROCESSED] {desc}",
                    "category":             category,
                    "subcategory":          subcategory,
                    "assignment_group":     group,
                    "ai_case_summary":      summary,
                    "ai_suggested_resolution": knowledge,
                    "ai_automation_notes":  auto_fix['notes'],
                    "ai_confidence_score":  confidence,
                    "status":               final_status
                }

                print("    [SERVICENOW] Updating record with AI Analysis...")
                if update_ticket(sys_id, payload):
                    print(f"    ✅ Processed: {desc[:40]}...")
                    print(f"       → Record : {sys_id}")
                    print(f"       → Action : {auto_fix['notes'][:60]}...")
                else:
                    print(f"    ❌ Failed to update {number}.")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[!] Polling service stopped.")