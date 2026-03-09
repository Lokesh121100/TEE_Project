# IntelSoft AI Service Desk — Project Overview

**Project**: IntelSoft AI Service Desk
**Purpose**: TEE (Technical Evaluation Exercise) — AI-powered IT Service Desk demo
**Stack**: FastAPI · Ollama/Llama3 · ServiceNow · Vanilla JS
**Status**: Production-ready demo

### Background

The TEE (Technical Evaluation Exercise) is a competitive evaluation where IntelSoft is demonstrating an AI-driven IT Service Desk solution to a client. The goal is to show how artificial intelligence can replace manual L1 ticket handling — classifying incidents, retrieving resolutions from a knowledge base, auto-resolving common issues, and escalating complex cases to human agents with full context. All AI inference runs on-premise using Ollama, meaning no user data is sent to any external cloud service.

---

## The Interface — 4 Sections

The web application at http://localhost:8000 has four sections accessible from the left sidebar:

**1. Service Desk**
The main interaction panel. A user types their IT problem (or picks from 10 quick scenario chips). The AI processes it in real-time — each reasoning step streams live to the screen. At the end, a ServiceNow ticket is created automatically. If the AI cannot resolve the issue, an "Escalate to Human Support" button appears, which opens a modal to send the case to a human agent with the full conversation transcript attached.

**2. Analytics**
Shows the 3-year strategic roadmap (Year 1: 22% deflection → Year 3: 72%), the AI classification confusion matrix (accuracy per category), and SLA breach prediction for open tickets.

**3. DEX Monitor (Device Experience)**
Shows health scores for 6 simulated devices (SID = Scientific workstations, CID = Corporate laptops). Scores fluctuate every 15 seconds. Each device has a one-click Remediate button. Also shows the Smart Locker dashboard (6 physical lockers for hardware replacement pickup) and a VPN Auto-Remediation panel with a 6-step diagnostic pipeline.

**4. Governance**
Shows the active AI safety controls (hallucination guard, bias mitigation, escalation rules, confidence threshold), the full audit trail of every AI decision, and the Cost and ROI projection panel.

---

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama (in a separate terminal)
ollama serve

# 3. Pull the Llama3 model (first time only)
ollama pull llama3

# 4. Start the server
python src/api/app.py

# App runs at http://localhost:8000
```

Environment variables are loaded from `.env` automatically. Copy `.env.example` to `.env` and fill in your credentials before running.

---

## Architecture

```
User Browser
    │
    ▼
FastAPI Server (src/api/app.py) — port 8000
    │
    ├── AI Agent (src/ai_agent/main.py)
    │       ├── NLU / Query Validation
    │       ├── Classification (poll_servicenow.py)
    │       ├── RAG — Knowledge Base (data/knowledge_base.json)
    │       ├── Auto-Resolution Engine
    │       └── Ollama/Llama3 (local LLM, no cloud)
    │
    ├── Governance (src/governance/)
    │       ├── Audit Logging
    │       ├── Bias Detection
    │       ├── Escalation Rules (9-rule engine)
    │       └── Cost Governance
    │
    └── ServiceNow REST API
            └── dev273008.service-now.com
                Table: x_1941577_tee_se_0_ai_incident_demo
```

**Data flow for each incident:**
1. User describes IT issue in plain language
2. AI validates it is IT-related (guardrail)
3. Checks 9 escalation rules — routes to human if triggered
4. Classifies: Category / Subcategory / Assignment Group / Confidence
5. Retrieves relevant Knowledge Base articles (RAG)
6. Runs zero-touch resolution if subcategory matches automation
7. Creates ServiceNow record with full AI reasoning attached
8. Streams each step live to the browser via SSE

---

## Key Files

| File | Purpose |
|---|---|
| `src/api/app.py` | FastAPI server — all API endpoints |
| `src/ai_agent/main.py` | AI core: NLU, RAG, resolution, ServiceNow |
| `src/ai_agent/poll_servicenow.py` | Classifier: keyword + LLM hybrid |
| `src/ai_agent/portal.py` | Gradio alternative UI |
| `src/frontend/index.html` | Main web UI (4 sections) |
| `src/frontend/app.js` | Frontend logic: streaming, DEX, locker |
| `src/governance/` | AI safety controls (5 modules) |
| `data/knowledge_base.json` | 10 RAG knowledge articles |
| `data/demo_cache.json` | Offline fallback responses |
| `data/ai_audit_logs.json` | AI decision audit trail |
| `accuracy_test.py` | 50-case benchmark — target 90% accuracy |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Ollama + ServiceNow status |
| GET | `/api/metrics` | Live metrics (pulls ticket count from ServiceNow) |
| GET | `/api/logs` | Audit trail HTML |
| POST | `/api/incident/stream` | SSE streaming — main incident processing |
| POST | `/api/incident` | Non-streaming fallback |
| POST | `/api/escalate` | Human escalation + ServiceNow ticket |
| GET | `/api/confusion-matrix` | Classification accuracy matrix |
| POST | `/api/sla-prediction` | SLA breach risk prediction |
| GET | `/api/device-health` | DEX device health (6 simulated devices) |
| POST | `/api/remediate` | Auto-remediate a device |
| POST | `/api/locker/assign` | Smart Locker assignment |

---

## What is Real vs Simulated

| Feature | Status | Notes |
|---|---|---|
| ServiceNow ticket creation | **Real** | Creates actual records |
| AI classification (NLU) | **Real** | Ollama/Llama3 running locally |
| RAG knowledge retrieval | **Real** | Searches knowledge_base.json |
| Audit logging | **Real** | Writes to ai_audit_logs.json |
| SSE streaming | **Real** | Live reasoning steps |
| Device health scores | **Simulated** | ±3 random fluctuation per API call |
| Auto-remediation | **Simulated** | Updates score in memory only |
| Smart Locker | **Simulated** | In-memory Python list |
| VPN pipeline | **Simulated** | Timed UI animation |
| MTTR / Satisfaction metrics | **Calculated** | Formula-based estimates |

---

## Production Path

| Now (Demo) | Production |
|---|---|
| Ollama on laptop | Ollama on company server or cloud VM |
| In-memory device state | Redis / PostgreSQL |
| File-based audit logs | Azure SQL / PostgreSQL |
| No authentication | Azure AD SSO / SAML |
| CORS open (`*`) | Restrict to company domain |
| Secrets in `.env` | Azure Key Vault |

**Real integrations to add for full production:**
- Device remediation → Microsoft Intune API
- Password reset → Azure Active Directory Graph API
- VPN fix → Cisco AnyConnect / Palo Alto API
- Smart Locker → Physical locker vendor API (Luxer One, etc.)
