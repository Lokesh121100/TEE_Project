#!/usr/bin/env python3
"""
ARIA v2.0 - TEE DEMO API (Simplified for testing without Ollama)
Uses pre-computed cached responses for all 10 scenarios
Run: python src/api/app_demo.py
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import json

app = FastAPI(title="ARIA v2.0 - TEE Demo")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load demo cache
DEMO_CACHE = {}
try:
    with open('data/demo_cache.json', 'r') as f:
        DEMO_CACHE = json.load(f).get('scenarios', {})
    print(f"[OK] Loaded {len(DEMO_CACHE)} demo scenarios from cache")
except Exception as e:
    print(f"[ERROR] Could not load demo cache: {e}")

# Mount frontend
frontend_dir = os.path.join(os.getcwd(), 'src', 'frontend')
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve frontend"""
    index_path = os.path.join(frontend_dir, 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            return f.read()
    return "<h1>Frontend not found</h1>"

@app.get("/api/health")
async def health_check():
    """Health check"""
    return {
        "ollama": "🟢 Online (Demo Mode)",
        "model": "🟢 Llama3 Ready (Cached)",
        "servicenow": "🟢 Reachable"
    }

@app.post("/api/incident/demo")
async def create_incident_demo(request: Request):
    """DEMO: Test incident with cached response"""
    data = await request.json()
    scenario_id = str(data.get("scenario_id", ""))

    if not scenario_id or scenario_id not in DEMO_CACHE:
        return JSONResponse({"error": "Invalid scenario_id (1-10)"}, status_code=400)

    response_text = DEMO_CACHE[scenario_id]

    # Create simple HTML response
    result_html = f"""
    <div style='background-color: #0d1117; color: #c9d1d9; padding: 25px; border-radius: 12px; border: 1px solid #30363d;'>
        <h2 style='color: #3fb950; margin-top: 0;'>ARIA Response (Demo Mode - Scenario {scenario_id})</h2>
        <p style='background: #161b22; padding: 15px; border-radius: 6px; line-height: 1.6;'>
            {response_text}
        </p>
        <hr style='border: 0.5px solid #30363d;'>
        <p style='font-size: 0.85em; color: #58a6ff;'>Demo Mode - Pre-computed response</p>
    </div>
    """

    return {"result": result_html}

@app.post("/api/incident/stream")
async def create_incident_stream(request: Request):
    """SSE Stream - Demo mode"""
    data = await request.json()
    scenario_id = str(data.get("description", "1"))

    # Try to detect scenario from description
    scenario_map = {
        "password": "1",
        "vpn": "2",
        "slow": "3",
        "outlook": "4",
        "vdi": "5",
        "adobe": "6",
        "printer": "7",
        "wifi": "8",
        "damage": "9",
        "onboard": "10",
    }

    for keyword, sid in scenario_map.items():
        if keyword.lower() in data.get("description", "").lower():
            scenario_id = sid
            break

    def event_generator():
        # Simulate reasoning steps
        steps = [
            "AI Guardrail: Validating query relevance...",
            "AI Reasoning: Checking escalation triggers...",
            "AI Classification: Determining Category & Route...",
            "AI Synthesis: Generating Intelligent Case Summary...",
            "RAG: Retrieving best-match KB articles...",
            "Automation: Checking Zero-Touch eligibility...",
            "Platform: Creating ServiceNow Record...",
        ]

        for step in steps:
            payload = json.dumps({"step": step, "data": ""})
            yield f"data: {payload}\n\n"

        # Final result
        response_text = DEMO_CACHE.get(scenario_id, "Demo response for scenario " + scenario_id)
        result_html = f"""
        <div style='background-color: #0d1117; color: #c9d1d9; padding: 25px; border-radius: 12px; border: 1px solid #30363d;'>
            <h2 style='color: #3fb950; margin-top: 0;'>ARIA Response</h2>
            <p style='background: #161b22; padding: 15px; border-radius: 6px;'>{response_text}</p>
            <hr style='border: 0.5px solid #30363d;'>
            <p style='font-size: 0.85em; color: #58a6ff;'>Demo Mode - Pre-computed response</p>
        </div>
        """
        payload = json.dumps({"step": "done", "data": result_html})
        yield f"data: {payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("ARIA v2.0 - TEE DEMO API")
    print("="*60)
    print("\nMode: DEMO (Using cached responses)")
    print("Frontend: http://localhost:8000")
    print("Health: http://localhost:8000/api/health")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)
