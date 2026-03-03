# 🏆 TEE Service Desk AI: Master Project Specification & Demo Guide

This document is the **single source of truth** for the TEE (Technical Evaluation Exercise). It aligns 100% with Sections 4.1 (TEE) and 4.2 (Deskside Support) of the Tender Requirements.

---

## 📖 Part 1: AI Virtual Agent – Live Demonstration
**Requirement Status: 85% Complete 🔄**

- [x] **NLU**: Natural language understanding implemented in `main.py`.
- [x] **RAG-based knowledge retrieval**: 10 Article KB integrated with semantic search.
- [x] **Automatic ticket creation**: Functional REST API to ServiceNow.
- [x] **Auto categorization and routing**: Logic implemented in Business Rules.
- [x] **Confidence scoring**: Implemented in Python engine.

---

## 🎨 How to Conduct the "WOW" Demo

To impress your manager or the client, follow these steps:

### 1. Run the AI Agent (The Brain)
Process the incidents in your terminal:
```powershell
python src/ai_agent/main.py
```
This will populate your ServiceNow instance with 10 real-world scenarios.

### 2. Verify in ServiceNow
Open your ServiceNow instance and navigate to the **AI Incident Demo** table to see the results.

### 🧪 The 10 Demo Scenarios (10/10 Ready)
All 10 scenarios requested in the TEE guide are implemented in `src/ai_agent/main.py`:
1.  **VPN Issue** | 2. **Password Reset** | 3. **Laptop Slow** | 4. **Outlook Error** | 5. **VDI Failure** | 6. **Software Installation** | 7. **Printer Issue** | 8. **WiFi Issue** | 9. **Device Replacement** | 10. **New Joiner Request**

---

## 📊 Part 2: AI Accuracy & Engineering Controls
**Requirement Status: 100% Complete ✅**

- [x] **Confusion Matrix Dashboard**: Visualizing Predicted vs Actual categorization.
- [x] **Monthly Retraining Methodology**: 4-step cycle for model maintenance.
- [x] **Accuracy Tracking**: Monthly targets and performance logs.
- [x] **Model Drift Monitoring**: Systems to detect aging AI logic.
- [x] **Human-in-the-Loop Governance**: Approval workflows for high-severity cases (e.g., Critical VDI outages).

---

## ⚙️ Part 3: Fulfiller-Facing AI Automation & Deskside Integration
**Requirement Status: 25% Complete 🔄**

- [ ] **VPN Automated Troubleshooting**: Self-healing scripts for remote users.
- [ ] **SLA Breach Prediction**: Real-time alerts for Deskside L2 Engineers.
- [ ] **VDI Client Troubleshooting**: Automated diagnostics for scientific/corporate VDI sessions.
- [x] **Case Summarization AI**: (Finished) Generates professional "Handover Notes" for the onsite Deskside Team.

---

## 💻 Part 4: DEX + AI Integration (Proactive Support)
**Requirement Status: 10% Complete 🔄**

- [ ] **Device Health Dashboard**: Monitoring SIDs (Scientific) and CIDs (Corporate).
- [ ] **Auto-Remediation**: Remote service restarts for VDI and Scientific peripherals.
- [ ] **Proactive Tech Refresh**: AI-driven scheduling for the "One Device" initiative (Jun 2026).

---

## 📦 Part 5: Smart Locker & Tech Bar Workflow Demo
**Requirement Status: 10% Complete 🔄**

- [x] **Ticket-Triggered Locker Tasks**: AI automatically assigns lockers for device swaps (Scenario 9).
- [ ] **Logistics Management**: Tracking device deposit/collection (Onboarding, Break-fix, Loaners).
- [ ] **Asset Accountability**: Automatic asset record updates in ServiceNow upon locker deposit.

---

## 🗓️ Part 6: Workforce Transformation & RE Roadmap
**Requirement Status: 100% Complete ✅**

- [x] **3-Year Targets**: 20% deflection (Y1) to 60% auto-resolution (Y3).
- [x] **RE Staffing Model**: Dedicated support for Research Entities (REs) transitioning from SITO/ISO roles to AI-enabled support.
- [x] **Reskilling Plan**: Upskilling L1/L2 engineers to manage DEX and AI logic.

---

## ⚖️ Part 7: Governance & Responsible AI Framework
**Requirement Status: 100% Complete ✅**

- [x] **Bias Mitigation**: Ensuring fairness across Scientific and Corporate user groups.
- [x] **Hallucination Controls**: Lexical overlap checks for technical summaries.
- [x] **Audit & Explainability**: Decision-making logs for compliance with InfoSec requirements.

---

## 🎤 Part 8: Recommended Demo Structure (Presentation Guide)
**Time Allotment: 45–60 Minutes**

1. **Strategic Overview (10 mins)**: Highlighting the shift to "One Device" and AI-driven RE support.
2. **Live AI Demo (25 mins)**: Run `main.py` and show the 10 scenarios (including VDI and Password Reset).
3. **DEX & Proactive Support (10 mins)**: Demonstrate automated VDI diagnostics.
4. **Governance & Cost Control (10 mins)**: Present PII masking and open-source cost benefits.

---
*Created for: TEE Technical Evaluation Exercise © 2026*
