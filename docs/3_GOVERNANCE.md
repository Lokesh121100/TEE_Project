# IntelSoft AI Service Desk — Governance & Production Roadmap

---

## AI Governance Controls (Implemented)

### 1. Hallucination Guard
Every AI response is validated against Knowledge Base articles before delivery using lexical overlap scoring. If the response cannot be grounded in KB content, it is flagged and either suppressed or escalated.

### 2. Bias Mitigation — Personal Identifier Masking (PIM)
All user inputs are stripped of personal identifiers (names, employee IDs, demographic signals) before the AI processes them. Classification accuracy is monitored monthly per user segment.

### 3. Escalation Governance — 9-Rule Engine
Auto-escalation triggers on:
- Security-related keywords (data breach, phishing, ransomware)
- Recurring issues (same user, 3+ times in 7 days)
- Team-wide impact (5+ users affected)
- VIP users
- Out-of-hours critical requests
- Compliance-sensitive actions
- Confidence score below 70%
- Ambiguous intent detected
- Physical safety risk

### 4. Local Inference — On-Premise AI
Ollama/Llama3 runs entirely on the company's own hardware. Zero external API calls for AI inference. PII never leaves the network. Fully GDPR and InfoSec compliant.

### 5. Confidence Threshold
AI decisions below 70% confidence are automatically routed to L2 Senior Support — never auto-resolved. Threshold is configurable by the AI Governance Board.

### 6. Audit Trail
Every AI decision is written to `data/ai_audit_logs.json` with:
- Input description (masked)
- Predicted category / subcategory
- Confidence score
- Action taken (auto-resolved / escalated / routed)
- Timestamp
- ServiceNow record number

---

## Governance Structure

```
Executive Oversight (Monthly)
  └── CTO, CISO, Chief Compliance Officer

AI Governance Board (Bi-Weekly)
  └── AI Ops Manager, Legal, Ethics Officer,
      Security Officer, Service Desk Lead

AI Operations Team (Daily)
  └── AI Ops Specialist, ML Engineer, QA Engineer,
      Escalation Handler

Audit & Compliance (Weekly)
  └── Audit Log Reviewer, Bias Analyst,
      Compliance Validator
```

### Decision Rights

| Decision | Authority | Approval |
|---|---|---|
| Daily model tuning | AI Ops Manager | N/A |
| Model retraining | ML Engineer | CTO |
| Confidence threshold change | AI Ops Team | CISO |
| Escalation policy change | Business Owner | CCO |
| New automation subcategory | Product Manager | CTO + CISO |

---

## Monthly Retraining Cycle

To prevent model drift and maintain 90%+ accuracy:

1. **Extract** — Pull all incidents from the previous month where AI classification was overridden by a human
2. **Label** — Lead engineers review and assign ground truth categories
3. **Update prompts** — Add new edge cases to few-shot prompts in `poll_servicenow.py`
4. **Validate** — Run `python accuracy_test.py` — must pass 90% threshold before deployment
5. **Deploy** — Update model config, log retraining event in audit trail

**Drift Alert**: If AI predicted category vs human closed category diverges >15% over a 7-day rolling window, a Model Audit Task is auto-created in ServiceNow.

---

## 3-Year Workforce Transformation Roadmap

### Year 1 — AI-Assist (22% Deflection)
- AI handles: password resets, VPN basics, software install requests
- L1 agents focus on: complex issues, quality checks on AI resolutions
- Staff impact: no reduction — agents upskill to AI supervisors
- Training: 40-hour AI literacy programme for all service desk staff

### Year 2 — Automate (48% Deflection)
- AI handles: 15+ zero-touch subcategories
- New roles created: AI Trainer, Prompt Engineer, Quality Analyst
- Monthly retraining cycle fully operational
- L1 staff redeployed to: customer success, proactive outreach, training

### Year 3 — Autonomous (72% Deflection)
- Predictive healing via DEX — AI fixes issues before users notice
- AI manages full incident lifecycle for standard categories
- Staff focus: exception handling, AI governance, strategic projects
- Zero involuntary layoffs — all transitions via redeployment and upskilling

---

## Production Deployment Plan

### Phase 1 — Infrastructure (Month 1–2)

| Current (Demo) | Production |
|---|---|
| Ollama on laptop | Ollama on company server / Azure VM |
| `python src/api/app.py` | Docker container → Azure App Service |
| In-memory device state | Redis or PostgreSQL |
| File-based audit logs | Azure SQL / PostgreSQL |

**Recommended server spec for Ollama:**
- Minimum: 16GB RAM, 8-core CPU (CPU inference, ~5–10s response)
- Recommended: NVIDIA GPU with 8GB+ VRAM (GPU inference, ~1–2s response)

### Phase 2 — Real Integrations (Month 2–4)

| Simulated Feature | Real Integration | API |
|---|---|---|
| Device health | Microsoft Intune | Graph API — device telemetry |
| Auto-remediation | Intune + PowerShell | Endpoint Manager — run scripts on device |
| Password reset | Azure Active Directory | Graph API — one call, instant reset |
| VPN fix | Cisco AnyConnect | REST API — tunnel restart |
| Smart Locker | Physical locker vendor | Luxer One / Parcel Pending API |

### Phase 3 — Enterprise Hardening (Month 3–5)

- **Authentication**: Azure AD SSO / SAML (currently no login)
- **CORS**: Restrict from `*` to company domain only
- **Secrets**: Move from `.env` to Azure Key Vault
- **Monitoring**: Azure Monitor / Datadog — API latency, error rates, AI accuracy
- **Scaling**: Load balancer + multiple API replicas for high availability

### Estimated Costs (Production)

| Item | Monthly Cost |
|---|---|
| On-premise GPU server (amortised) | £200–400 |
| Azure App Service (API hosting) | £50–100 |
| Azure SQL (audit logs) | £30–60 |
| ServiceNow licence (existing) | existing |
| **Total** | **~£280–560/month** |

**ROI:**
- Value per auto-resolved ticket: $75 (vs $210 human agent)
- At 22% deflection on 1,720 tickets/month = 378 auto-resolved
- Annual savings: $129K
- Break-even: Month 4
