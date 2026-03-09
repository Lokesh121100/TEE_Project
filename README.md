# IntelSoft AI Service Desk

An AI-powered IT Service Desk built for the Technical Evaluation Exercise (TEE). The system classifies IT incidents, retrieves relevant knowledge, auto-resolves common issues, and creates ServiceNow records — all in real-time via a browser-based interface.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start Ollama (separate terminal)
ollama serve

# Pull the model (first time only)
ollama pull llama3

# Start the server
python src/api/app.py
```

Application runs at http://localhost:8000

Copy `.env.example` to `.env` and add your ServiceNow credentials before starting.

---

## What It Does

The system processes a plain-language IT issue description through 8 sequential steps, each streamed live to the browser:

1. Validates the query is IT-related (guardrail)
2. Checks 9 escalation rules — routes to human if triggered
3. Classifies into category, subcategory, and assignment group
4. Scores confidence (escalates automatically if below 70%)
5. Retrieves matching Knowledge Base articles via RAG
6. Runs zero-touch resolution for supported subcategories
7. Creates a ServiceNow incident with full AI reasoning attached
8. Logs the decision to the audit trail

---

## Project Structure

```
src/
  api/app.py               — FastAPI server, all endpoints (port 8000)
  ai_agent/main.py         — AI core: NLU, RAG, resolution, ServiceNow
  ai_agent/poll_servicenow.py — Classifier: keyword + LLM hybrid
  ai_agent/portal.py       — Gradio alternative UI
  frontend/                — index.html, app.js, styles.css
  governance/              — Audit logging, bias detection, escalation rules,
                             cost governance (5 modules)

data/
  knowledge_base.json      — 10 RAG articles covering all scenario types
  demo_cache.json          — Offline fallback responses
  ai_audit_logs.json       — AI decision audit trail

docs/
  1_OVERVIEW.md            — Architecture, API reference, real vs simulated
  2_DEMO_GUIDE.md          — 45-min demo script, scenarios, Q&A answers
  3_GOVERNANCE.md          — AI controls, governance structure, production roadmap

accuracy_test.py           — 50-case benchmark, target 90% accuracy
```

---

## Demo Scenarios

Ten scenarios are available as quick-select chips on the Service Desk tab:

| Scenario | Category | Auto-Resolved |
|---|---|---|
| Password Reset | Access | Yes |
| VPN Issue | Network | Partial |
| Slow Laptop | Hardware | Partial |
| Outlook Error | Software | No |
| VDI Failure | Network | No |
| Software Install | Software | No |
| Printer Error | Hardware | No |
| WiFi Issue | Network | No |
| Device Damage | Hardware | No — triggers Smart Locker |
| New Joiner | Access | No — triggers provisioning flow |

---

## Documentation

| File | Contents |
|---|---|
| [docs/1_OVERVIEW.md](docs/1_OVERVIEW.md) | Architecture, API endpoints, key files, production path |
| [docs/2_DEMO_GUIDE.md](docs/2_DEMO_GUIDE.md) | Demo script, scenario talking points, Q&A preparation |
| [docs/3_GOVERNANCE.md](docs/3_GOVERNANCE.md) | AI controls, governance model, 3-year roadmap, deployment plan |

---

## Technology Stack

| Layer | Technology |
|---|---|
| AI Inference | Ollama + Llama3 (local, on-premise) |
| Backend | FastAPI (Python) |
| Frontend | Vanilla JS, HTML, CSS |
| Ticketing | ServiceNow REST API |
| Knowledge Retrieval | RAG over JSON knowledge base |
| Alternative UI | Gradio (portal.py) |

---

*IntelSoft AI Service Desk — TEE Technical Evaluation Exercise 2026*
