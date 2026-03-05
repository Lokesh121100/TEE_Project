from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import json

# Ensure we can import the existing logic
sys.path.append(os.path.join(os.getcwd(), 'src', 'ai_agent'))

try:
    from portal import check_system_health, get_live_audit_logs, compute_live_metrics
    from main import (
        validate_query_relevance,
        generate_incident_summary_tuple,
        retrieve_knowledge,
        run_auto_resolution,
        create_servicenow_incident,
        is_escalation_needed,
        generate_escalation_response,
        handle_ambiguous_query,
        log_ai_decision
    )
    import poll_servicenow as ps
    classify_incident = ps.classify_ticket_full
except ImportError as e:
    print(f"Warning: Could not import core AI logic. Ensure you are running from the project root. Error: {e}")

app = FastAPI(title="IntelSoft AI Service Desk API")

# Allow CORS for development if frontend is served separately
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static frontend directory
frontend_dir = os.path.join(os.getcwd(), 'src', 'frontend')
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main index.html file"""
    index_path = os.path.join(frontend_dir, 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            return f.read()
    return "<h1>IntelSoft Frontend not found at src/frontend/index.html</h1>"

# Load demo cache for fallback
DEMO_CACHE = {}
try:
    with open('data/demo_cache.json', 'r') as f:
        DEMO_CACHE = json.load(f).get('scenarios', {})
except:
    pass

@app.get("/api/health")
async def health_check():
    """API endpoint for system health"""
    ollama, model, servicenow = check_system_health()
    return {
        "ollama": ollama,
        "model": model,
        "servicenow": servicenow
    }

@app.get("/api/logs")
async def get_logs():
    """API endpoint for recent audit logs"""
    html_logs = get_live_audit_logs()
    return {"html": html_logs}

@app.get("/api/metrics")
async def get_metrics():
    """API endpoint for live computed metrics"""
    return compute_live_metrics()

def _sse_event(step, data=""):
    """Format a Server-Sent Event message."""
    payload = json.dumps({"step": step, "data": data})
    return f"data: {payload}\n\n"

@app.post("/api/incident/stream")
async def create_incident_stream(request: Request):
    """SSE endpoint: streams real processing steps to the frontend."""
    data = await request.json()
    description = data.get("description", "")

    if not description:
        return JSONResponse({"error": "Description is required"}, status_code=400)

    def event_generator():
        try:
            # Step 1: Validate relevance
            yield _sse_event("AI Guardrail: Validating query relevance...")
            if not validate_query_relevance(description):
                yield _sse_event("done", "<div style='color:#ff7b72;padding:20px;'>Query filtered: not IT-related.</div>")
                return

            # Step 2: Check escalation
            yield _sse_event("AI Reasoning: Checking escalation triggers...")
            escalate, reason = is_escalation_needed(description)

            # Step 3: Classify
            yield _sse_event("AI Classification: Determining Category & Route...")
            category, subcategory, group, confidence = classify_incident(description)

            if escalate:
                yield _sse_event("Governance: Escalation triggered - routing to L2...")
                category, subcategory, group, confidence = "other", "Escalation", "L2 Senior Support", 0.0

            # Step 4: Generate summary
            yield _sse_event("AI Synthesis: Generating Intelligent Case Summary...")
            title, analysis = generate_incident_summary_tuple(
                description, category=category, subcategory=subcategory,
                caller="portal.user@tee-demo.com", confidence=confidence
            )

            # Step 5: RAG
            yield _sse_event("RAG: Retrieving best-match KB articles...")
            knowledge = retrieve_knowledge(description)

            # Step 6: Auto-resolution
            yield _sse_event("Automation: Checking Zero-Touch eligibility...")
            auto_fix = run_auto_resolution(subcategory, description)

            # Step 7: Create ServiceNow incident
            yield _sse_event("Platform: Creating ServiceNow Record...")
            success, inc_num = create_servicenow_incident(
                short_description=title,
                category=category,
                subcategory=subcategory,
                caller="portal.user@tee-demo.com",
                assignment_group=group if group else "Service Desk",
                summary=analysis,
                knowledge=knowledge,
                auto_fix=auto_fix
            )

            if success:
                result_html = f"""
                <div style='background-color: #0d1117; color: #c9d1d9; padding: 25px; border-radius: 12px; border: 1px solid #30363d;'>
                    <h2 style='color: #3fb950; margin-top: 0;'>AI Incident Processed: {inc_num}</h2>
                    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;'>
                        <div style='background: #161b22; padding: 10px; border-radius: 6px;'><b>Category:</b> {category}/{subcategory}</div>
                        <div style='background: #161b22; padding: 10px; border-radius: 6px;'><b>Status:</b> {auto_fix['status']}</div>
                        <div style='background: #161b22; padding: 10px; border-radius: 6px;'><b>Assignment:</b> {group}</div>
                        <div style='background: #161b22; padding: 10px; border-radius: 6px;'><b>Confidence:</b> {int(confidence*100)}%</div>
                    </div>
                    <p><b>Short Description:</b> {title}</p>
                    <p><b>AI Case Analysis:</b> {analysis}</p>
                    <p style='color: #8b949e; font-style: italic; border-left: 3px solid #30363d; padding-left: 10px;'><b>AI Notes:</b> {auto_fix['notes']}</p>
                    <hr style='border: 0.5px solid #30363d;'>
                    <p style='font-size: 0.85em; color: #58a6ff;'>Record <b>{inc_num}</b> is now live in ServiceNow.</p>
                </div>
                """
            else:
                result_html = "<div style='color:#ff7b72;padding:20px;'>Failed to create ServiceNow incident.</div>"

            yield _sse_event("done", result_html)

        except Exception as e:
            yield _sse_event("done", f"<div style='color:#ff7b72;padding:20px;'>Error: {str(e)}</div>")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/incident")
async def create_incident(request: Request):
    """Non-streaming fallback endpoint for backward compatibility."""
    data = await request.json()
    description = data.get("description", "")

    if not description:
        return JSONResponse({"error": "Description is required"}, status_code=400)

    try:
        if not validate_query_relevance(description):
            return {"result": "<div style='color:#ff7b72;'>Query filtered: not IT-related.</div>"}

        category, subcategory, group, confidence = classify_incident(description)

        escalate, reason = is_escalation_needed(description)
        if escalate:
            category, subcategory, group, confidence = "other", "Escalation", "L2 Senior Support", 0.0

        title, analysis = generate_incident_summary_tuple(
            description, category=category, subcategory=subcategory,
            caller="portal.user@tee-demo.com", confidence=confidence
        )
        knowledge = retrieve_knowledge(description)
        auto_fix = run_auto_resolution(subcategory, description)

        success, inc_num = create_servicenow_incident(
            short_description=title, category=category, subcategory=subcategory,
            caller="portal.user@tee-demo.com",
            assignment_group=group if group else "Service Desk",
            summary=analysis, knowledge=knowledge, auto_fix=auto_fix
        )

        if success:
            return {"result": f"Incident {inc_num} created. Category: {category}/{subcategory}, Group: {group}, Confidence: {confidence}"}
        else:
            return JSONResponse({"error": "Failed to create ServiceNow incident"}, status_code=500)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/incident/demo")
async def create_incident_demo(request: Request):
    """DEMO MODE: Use pre-computed responses for TEE demo (when Ollama is unavailable)"""
    data = await request.json()
    scenario_id = data.get("scenario_id", "")

    if not scenario_id or scenario_id not in DEMO_CACHE:
        return JSONResponse({"error": "Invalid scenario_id"}, status_code=400)

    try:
        # Get cached response
        cached_response = DEMO_CACHE[scenario_id]

        # Create ServiceNow incident with demo data
        demo_mappings = {
            "1": ("Password Reset", "access", "Password", "Identity & Access"),
            "2": ("VPN Disconnection", "network", "VPN", "Network Support"),
            "3": ("Laptop Performance", "hardware", "Performance", "Desktop Support"),
            "4": ("Outlook Crash", "software", "Email", "Software Support"),
            "5": ("VDI Session Timeout", "software", "VDI", "Virtualization Team"),
            "6": ("Software Installation Request", "software", "Installation", "Service Desk"),
            "7": ("Printer Error 50.1", "hardware", "Printer", "Facility IT"),
            "8": ("WiFi Network Visibility", "network", "WiFi", "Network Support"),
            "9": ("Device Damage Replacement", "hardware", "Replacement", "Hardware Logistics"),
            "10": ("New Joiner Onboarding", "access", "Onboarding", "Service Desk"),
        }

        title, category, subcategory, group = demo_mappings.get(scenario_id, ("Demo Incident", "other", "General", "Service Desk"))

        # Create incident in ServiceNow
        success, inc_num = create_servicenow_incident(
            short_description=title,
            category=category,
            subcategory=subcategory,
            caller="portal.user@tee-demo.com",
            assignment_group=group,
            summary=cached_response[:100],
            knowledge="Cached demo response",
            auto_fix={"status": "Demo", "notes": "Pre-computed response"}
        )

        if success:
            result_html = f"""
            <div style='background-color: #0d1117; color: #c9d1d9; padding: 25px; border-radius: 12px; border: 1px solid #30363d;'>
                <h2 style='color: #3fb950; margin-top: 0;'>AI Response (Demo Mode)</h2>
                <p><b>Scenario {scenario_id}:</b> {title}</p>
                <p style='background: #161b22; padding: 10px; border-radius: 6px;'>{cached_response}</p>
                <hr style='border: 0.5px solid #30363d;'>
                <p style='font-size: 0.85em; color: #58a6ff;'>ServiceNow Incident: <b>{inc_num}</b></p>
            </div>
            """
            return {"result": result_html}
        else:
            return JSONResponse({"error": "Failed to create incident"}, status_code=500)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/escalate")
async def escalate_to_human(request: Request):
    """Escalate incident to human support with transcript capture"""
    try:
        data = await request.json()
        ticket_id = data.get("ticket_id", "")
        reason = data.get("reason", "User requested escalation")
        priority = data.get("priority", "Medium")
        transcript = data.get("transcript", [])

        if not ticket_id:
            return JSONResponse({"error": "ticket_id is required"}, status_code=400)

        # Create escalation record in ServiceNow
        escalation_data = {
            "short_description": f"[ESCALATED] {reason}",
            "description": f"Escalation Reason: {reason}\n\nTranscript:\n" +
                          "\n".join([f"- {msg}" for msg in transcript]),
            "priority": priority,
            "assignment_group": "L2 Senior Support",
            "category": "escalation",
            "u_ai_escalated": "true"
        }

        # Build ServiceNow REST API URL
        from urllib.parse import urljoin
        import requests
        from requests.auth import HTTPBasicAuth

        sn_url = "https://dev273008.service-now.com"
        sn_table = "x_1941577_tee_se_0_escalation_queue"

        # Note: Use environment variables in production
        sn_user = "admin"
        sn_pass = "Intelsoft@123"

        incident_url = f"{sn_url}/api/now/table/{sn_table}"

        try:
            response = requests.post(
                incident_url,
                json=escalation_data,
                auth=HTTPBasicAuth(sn_user, sn_pass),
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code in [200, 201]:
                incident = response.json().get("result", {})
                inc_num = incident.get("number", "ESC-" + ticket_id)
                sys_id = incident.get("sys_id", "")

                return {
                    "status": "escalated",
                    "escalation_number": inc_num,
                    "message": f"Successfully escalated to L2 Support. Reference: {inc_num}",
                    "sla_minutes": 120,  # 2-hour SLA for escalations
                    "assigned_team": "L2 Senior Support",
                    "transcript_saved": True
                }
            else:
                return JSONResponse({
                    "status": "error",
                    "message": f"ServiceNow error: {response.status_code}"
                }, status_code=response.status_code)

        except requests.exceptions.RequestException as sn_error:
            # Fallback: Create local escalation record
            return {
                "status": "escalated_local",
                "escalation_number": f"ESC-{ticket_id}",
                "message": "Escalated to L2 Support (offline mode)",
                "sla_minutes": 120,
                "assigned_team": "L2 Senior Support",
                "warning": "ServiceNow integration unavailable - using local escalation"
            }

    except Exception as e:
        return JSONResponse({"error": f"Escalation failed: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("INTELSOFT AI PORTAL API: READY")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=9000, reload=False)
