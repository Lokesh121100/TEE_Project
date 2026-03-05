# 🧪 TEE Project: Manual Testing & Project Status Guide

**Project Name**: ARIA v2.0 (AI Service Desk)
**Status**: ✅ 100% COMPLETE & READY FOR TESTING
**Date**: March 2026

---

## 📊 PROJECT STATUS OVERVIEW

### ✅ What's Been Completed

| Component | Status | Details |
|-----------|--------|---------|
| **AI Agent Logic** | ✅ Done | NLU, RAG, categorization, confidence scoring |
| **Frontend (Web UI)** | ✅ Done | ARIA v2.0 dashboard with real-time streaming |
| **API Server** | ✅ Done | FastAPI with SSE streaming |
| **ServiceNow Integration** | ✅ Done | Auto-create incidents with categorization |
| **Ollama Integration** | ✅ Done | Llama3 model for AI reasoning |
| **Knowledge Base** | ✅ Done | 10 KB articles for RAG |
| **Audit Logging** | ✅ Done | Track all AI decisions |
| **Governance Controls** | ✅ Done | Escalation rules, bias mitigation, hallucination guards |

---

## 🚀 HOW TO TEST MANUALLY

### **Step 1: Start Ollama (The AI Brain)**
```bash
# Start Ollama in a terminal
ollama serve

# (In a new terminal) Pull Llama3 model if not already present:
ollama pull llama3
```
**Status Check**: Open http://localhost:11434/api/tags to verify Ollama is running.

---

### **Step 2: Start the FastAPI Server (The Backend)**
```bash
cd C:\Users\lokes\Documents\TEE_Project

# Start the API server
python src/api/app.py
```

**Expected Output**:
```
==================================================
INTELSOFT AI PORTAL API: READY
==================================================
```

**Server Running At**: `http://localhost:8000`

---

### **Step 3: Open the Web Interface**
Open in your browser:
```
http://localhost:8000/
```

**You should see**:
- ARIA v2.0 dashboard
- Left sidebar with navigation
- Input form to "Describe your IT issue"
- Real-time AI reasoning panel on the right
- System health status (Ollama, Llama3, ServiceNow)

---

### **Step 4: Test the AI with Demo Scenarios**

Click **"Quick scenarios"** buttons or manually enter an issue:

#### **Scenario 1: VPN Issue** (AutoFix Eligible)
```
My VPN keeps disconnecting every few minutes while working from home
```
**Expected Result**:
- Category: Network
- Subcategory: VPN
- Auto-resolved: Yes
- ServiceNow Incident Created: ✓

#### **Scenario 2: Password Reset** (AutoFix Eligible)
```
I forgot my password and cannot login to my computer
```
**Expected Result**:
- Category: Access
- Subcategory: Password Reset
- Auto-resolved: Yes
- Status: "Resolved - Pending Confirmation"

#### **Scenario 3: Slow Laptop** (Requires L2 Support)
```
My laptop is running extremely slow and takes 10 minutes to boot
```
**Expected Result**:
- Category: Hardware
- Subcategory: Performance
- Auto-resolved: No (requires technician)
- Routed to: L1 Support

#### **Scenario 4: Outlook Error** (Complex - May Escalate)
```
Outlook crashes when I try to attach a PDF document
```
**Expected Result**:
- Category: Software
- Subcategory: Microsoft Office
- Confidence: Check if low (<70%) → triggers human review

---

## 🔌 ServiceNow Integration (What You Need to Know)

### **What is ServiceNow?**
- Enterprise IT Service Management platform
- Stores all incidents, tickets, and requests
- Our AI automatically creates tickets there
- You can view results in your ServiceNow instance

### **Your ServiceNow Instance**
```
URL: https://dev273008.service-now.com
User: admin
Password: @nL=BMhj07Sk
Table: x_1941577_tee_se_0_ai_incident_demo
```

### **How to View Created Incidents in ServiceNow**

**Method 1: Web UI**
1. Log in to https://dev273008.service-now.com
2. Search for: `AI Incident Demo` table
3. Click to view all incidents created by ARIA

**Method 2: View via API**
```bash
curl -u admin:@nL=BMhj07Sk "https://dev273008.service-now.com/api/now/table/x_1941577_tee_se_0_ai_incident_demo?sysparm_limit=5"
```

### **What Info Gets Stored**
- **Short Description**: AI-generated title
- **Category/Subcategory**: AI classification
- **Confidence Score**: How sure the AI is
- **Auto-Fix Status**: Was it auto-resolved?
- **Audit Trail**: Why AI made this decision
- **Knowledge Articles**: RAG recommendations

---

## 📋 TESTING CHECKLIST

Use this to verify everything works:

```
Frontend:
  ☐ Web dashboard loads at http://localhost:8000/
  ☐ Sidebar navigation works
  ☐ "Service Desk" tab displays
  ☐ "Analytics" and "Governance" tabs are clickable

AI Processing:
  ☐ Can submit incident description
  ☐ Real-time reasoning steps appear (streaming)
  ☐ AI responds with categorization
  ☐ Confidence score is displayed
  ☐ Auto-fix suggestion appears

System Health:
  ☐ Ollama shows as "Online" (green dot)
  ☐ Llama3 shows as "Ready" (green dot)
  ☐ ServiceNow shows as "Reachable" (green dot)

Metrics Display:
  ☐ MTTR Reduction % shows
  ☐ Classification Accuracy % shows
  ☐ User Satisfaction % shows
  ☐ Tickets Processed count shows

ServiceNow Integration:
  ☐ Incident created in ServiceNow
  ☐ Title matches AI summary
  ☐ Category/Subcategory correctly set
  ☐ Confidence score recorded

Escalation Logic:
  ☐ Low confidence (<70%) triggers "Human Review"
  ☐ Complex issues route to L2 Support
  ☐ Security issues escalate to "Security Team"
```

---

## 🛠️ TROUBLESHOOTING

### **Problem 1: "Cannot connect to Ollama"**
```
Error: HTTPConnectionPool(host='localhost', port=11434)
```
**Solution**:
- Make sure Ollama is running: `ollama serve`
- Check: http://localhost:11434/api/tags
- If not running, install from: https://ollama.com

---

### **Problem 2: "Llama3 model not found"**
```
Error: 'llama3' not in available models
```
**Solution**:
```bash
ollama pull llama3
ollama list  # Should show llama3:latest
```

---

### **Problem 3: API returns 404**
**Solution**:
- Make sure API server is running: `python src/api/app.py`
- Check all endpoints are responding: `curl http://localhost:8000/api/health`

---

### **Problem 4: Cannot connect to ServiceNow**
```
Error: Authentication failed or URL unreachable
```
**Solution**:
- Verify credentials are correct in `src/api/app.py`
- Check internet connection
- Verify ServiceNow instance is active
- Test manually: `curl -u admin:password "https://dev273008.service-now.com/api/now/table/..."`

---

## 📈 KEY METRICS TO MONITOR

After running tests, check the dashboard for:

| Metric | What It Means |
|--------|---------------|
| **MTTR Reduction** | How much faster AI resolves issues (target: 40%) |
| **Classification Accuracy** | % of correct category assignments (target: 90%+) |
| **User Satisfaction** | Customer satisfaction score (target: 4.5/5) |
| **Tickets Processed** | Total incidents handled (cumulative) |

---

## 🎯 QUICK TEST SCRIPT

Run this to automate testing (if you want):
```bash
python run_tests.py
```

This will:
- Test all AI functions
- Verify ServiceNow connection
- Check KB retrieval
- Validate categorization accuracy
- Generate a detailed test report

---

## 📞 SUPPORT

If you hit issues:
1. Check this guide's Troubleshooting section
2. Review the ARCHITECTURE.md for technical details
3. Check the latest commit messages: `git log --oneline | head -5`
4. View API logs: Check terminal where API is running

---

**Status**: ✅ All systems ready for evaluation
**Last Updated**: March 5, 2026
