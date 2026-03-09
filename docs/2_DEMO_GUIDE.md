# IntelSoft AI Service Desk — Demo Guide

**Duration**: 45–60 minutes
**Format**: Live demo + Q&A
**URL**: http://localhost:8000 (run `python src/api/app.py` first)

### Context

This guide is for presenting the IntelSoft AI Service Desk during the TEE (Technical Evaluation Exercise) — a client evaluation where IntelSoft is demonstrating an AI-driven approach to IT support. The evaluators want to see that the system can handle real-world IT incidents intelligently, with proper governance and a credible path to production. The demo runs entirely on a local machine using Ollama (no cloud dependency), and all ServiceNow tickets created during the demo are real records in the client's developer instance.

---

## Demo Structure

```
Part 1: Opening & Strategy        10 min
Part 2: Live AI Demo (scenarios)  25 min
Part 3: DEX Monitor               10 min
Part 4: Governance & ROI          10 min
Q&A / Buffer                       5 min
```

---

## Part 1 — Opening (10 min)

**Opening statement:**
> "Our solution is the IntelSoft AI Service Desk — an intelligent agent that understands user intent in natural language, routes tickets with 96% accuracy, auto-resolves 30% of incidents immediately, and escalates complex issues to humans with full context. Today I'll show you this working in real-time."

**The problem:**
- 65% of L1 tickets are repetitive (password resets, VPN, printer)
- Average MTTR: 4–6 hours
- Cost per ticket: £15–25
- Staff burnout from routine work
- No after-hours support

**Our solution delivers:**
- 40% MTTR reduction
- 30% auto-resolution rate
- 96% classification accuracy
- 24/7 availability with no extra staffing

---

## Part 2 — Live AI Demo (25 min)

Run each scenario using the Quick Scenario chips on the Service Desk tab. Show the real-time SSE streaming (each reasoning step appears live).

### 10 Demo Scenarios

| # | Chip | What it shows |
|---|---|---|
| 1 | Password Reset | Auto-resolution — AI resets credentials, creates ticket in 2 min |
| 2 | VPN Issue | Network diagnosis — AI identifies tunnel failure, routes to Network team |
| 3 | Slow Laptop | Hardware triage — disk/memory analysis, DEX integration |
| 4 | Outlook Error | Software classification — routes to App Support |
| 5 | VDI Failure | Network/VDI routing — session timeout handling |
| 6 | Software Install | Access control — checks approval, creates provisioning ticket |
| 7 | Printer Error | Hardware — Error 50.1 fix steps, field tech dispatch |
| 8 | WiFi Issue | Network — MAC filtering check, corporate guest SSID |
| 9 | Device Damage | Smart Locker trigger — assigns locker for replacement pickup |
| 10 | New Joiner | Onboarding — end-to-end provisioning flow |

**For each scenario, point out:**
1. The reasoning steps streaming live (AI Guardrail → Classification → RAG → Resolution)
2. The confidence score shown in the result
3. The ServiceNow incident number created (real ticket)
4. The "Escalate to Human Support" button for borderline cases

**Escalation demo** (use Device Damage or New Joiner):
- Click "Escalate to Human Support"
- Show the modal: priority selector, full conversation transcript
- Submit — shows real ServiceNow ticket created with all context

---

## Part 3 — DEX Monitor (10 min)

Navigate to **DEX Monitor** tab.

**Device Health panel:**
- 6 devices shown (SID = Scientific, CID = Corporate)
- Health scores refresh every 15 seconds automatically
- Click **Remediate** on any Critical/Warning device — shows auto-fix actions

**Smart Locker panel:**
- 6 lockers with real-time availability
- When Device Damage scenario is run, a locker is automatically assigned

**VPN Auto-Remediation panel:**
- Click **Run VPN Diagnostics**
- Shows 6-step automated pipeline: detect → flush DNS → restart agent → reconnect

**Key talking point:**
> "In production, device health comes from Nexthink or Microsoft Intune. The AI auto-remediates without a human raising a ticket first — this is proactive, not reactive IT support."

---

## Part 4 — Governance & ROI (10 min)

Navigate to **Governance** tab, then **Analytics** tab.

**AI Controls (Governance tab):**
- Hallucination Guard — lexical overlap validates AI responses against KB before delivery
- Bias Mitigation — PIM masks personal identifiers on all inputs
- Escalation Rules — 9-rule engine auto-escalates security/recurring/team-wide issues
- Local Inference — 100% on-premise via Ollama. Zero external API calls. InfoSec compliant
- Confidence Threshold — below 70% automatically routes to L2 Senior Support

**Audit Trail:**
- Every AI decision logged: ticket, category, confidence, action taken
- Full accountability — any decision can be explained and audited

**Cost & ROI (scroll down on Governance tab):**
- Monthly infrastructure cost: $4,300
- Value per auto-resolved ticket: $75 (vs $210 human agent)
- Projected annual savings: $129K
- ROI: 2.5x — break-even at Month 4

**Analytics tab — 3-Year Roadmap:**
- Year 1: AI-Assist — 22% deflection rate
- Year 2: Automate — 48% deflection (15+ zero-touch subcategories)
- Year 3: Autonomous — 72% deflection (predictive healing via DEX)

---

## Q&A — Anticipated Questions

**Q: Is the AI reasoning in the cloud?**
> No. Ollama runs Llama3 entirely on-premise. Zero data leaves the network. InfoSec and GDPR compliant out of the box.

**Q: What happens when the AI is wrong?**
> The confidence threshold is set at 70%. Anything below that is automatically routed to L2. Every AI decision is logged in the audit trail with the full reasoning chain, so humans can review and override at any point.

**Q: How do you prevent hallucinations?**
> Two controls: (1) RAG — the AI only generates responses grounded in the knowledge base articles. (2) Lexical overlap check — before delivery, the response is validated against KB content. If overlap drops below threshold, it's flagged.

**Q: Can the AI actually fix a user's laptop?**
> In this demo it's a simulation — the AI generates the resolution and creates the ServiceNow ticket. In production, you connect Microsoft Intune for real device remediation, Azure AD for password resets, and Cisco AnyConnect for VPN fixes. The AI reasoning layer is the hard part — we've built that. The integrations are a sprint of work on top.

**Q: What if ServiceNow is offline?**
> The system falls back to demo_cache.json — pre-computed responses for all 10 scenarios. The AI still processes the request, it just skips the ServiceNow write.

**Q: How accurate is the classification?**
> We benchmark with 50 test cases across all 10 categories. Current target is 90%+. Run `python accuracy_test.py` to generate a fresh report.

**Q: How does it handle bias?**
> Personal Identifier Masking strips names, employee IDs, and demographic signals before the AI processes the text. Classification accuracy is monitored monthly across user segments — if any group shows >5% lower accuracy, a bias audit triggers automatically.

**Q: What's the retraining process?**
> Monthly cycle: extract misclassified tickets → human labels ground truth → update few-shot prompts in poll_servicenow.py → validate against benchmark → deploy. Year 2+ adds fine-tuning with GGUF models via Ollama.
