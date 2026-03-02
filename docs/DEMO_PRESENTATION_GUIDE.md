# TEE Demo Presentation Guide: AI Service Desk Automation

To deliver a high-impact demo to your client/evaluators, follow this structured 4-part flow.

---

## Part 1: The "Why" (5 Mins) - Slide/Talk
*   **The Problem**: IT desks are overwhelmed with repetitive tickets (Password Reset, VPN).
*   **Our Solution**: An "Autonomous Service Desk" that uses private, open-source AI to categorize, summarize, and route incidents in < 2 seconds.
*   **The Edge**: **$0 API Cost** (No OpenAI/Google cloud fees) and **Platform-Side Intelligence** (ServiceNow rules).

---

## IMPORTANT: Why show VS Code?
The client needs to see **VS Code** for only 1 minute to prove that **AI** is doing the work. If you only show ServiceNow, they might think you typed the ticket yourself. VS Code is your "Proof of AI."

**The "Business-First" Strategy**: Keep ServiceNow open in your browser 90% of the time. Only switch to VS Code to "Start the AI Robot."

---

## Part 2: The Live Action (10 Mins)
*   **Visual Setup**: Arrange your screen in a **Split View**.
    *   **Left Side**: VS Code with `src/ai_agent/main.py` open.
    *   **Right Side**: An open Terminal (integrated in VS Code).
*   **Step 1: Open the Script**
    *   Highlight these lines in `main.py`:
        1.  The `pipeline("summarization")` - Tell them: *"This is the brain."*
        2.  The `scenarios` list - Tell them: *"These are the real-world problems we solved."*
*   **Step 2: Run the Demo**
    *   In the terminal, run: `python src/ai_agent/main.py`
    *   **The "Story"**: *"Watch the terminal. The AI is reading the raw text, filtering out the noise, and determining the priority level."*
*   **Step 3: Verification**
    *   Wait for the "Incident Created Successfully" message.
    *   **Tell them**: *"Notice the status code 201. This means ServiceNow has officially accepted our AI's data."*

---

## Part 3: The "Magic" in ServiceNow (10 Mins)
*   **Step 1: Show the Incidents**
    *   Open your ServiceNow instance (`dev273008.service-now.com`).
    *   Navigate to the **TEE Service Desk AI** app -> **AI Incident Demo** table.
*   **Step 2: Show the Automation**
    *   Open one of the newly created incidents.
    *   **Focus on the "Assignment Group"**: Show that it's already assigned (e.g., to "Network Support").
    *   **The Reveal**: Explain that the **Business Rule** we deployed (`AI Auto-Assignment`) did this routing automatically inside the platform.

---

## Part 4: The 3-Year Vision (5 Mins)
*   **The Roadmap**: Show that this is just Phase 1. 
    *   **Year 1**: Auto-categorization (What we showed today).
    *   **Year 2**: Auto-remediation (e.g., the script actually resets the password).
    *   **Year 3**: Predictive analytics (Preventing issues before they happen).

---

## Part 5: The "Fail-Safe" Strategy (No Live Code)
If you are worried about running the script live, you can show the demo using **Pre-Recorded Visuals**. This is 100% safe and still looks professional.

### Option A: The "Pre-Recorded Story" (Recommended)
1.  **Record a Video**: Use a screen recorder (like Windows + G) to record yourself running the script and then refreshing ServiceNow.
2.  **The Benefit**: You can talk over the video without worrying about the internet or the computer being slow.

### Option B: The "Success Stories" (Static)
1.  **Pre-populate ServiceNow**: Run the script 5-10 times *before* the meeting.
2.  **Show the Dashboard**: Open the [AI Analytics Dashboard](file:///c:/Users/lokes/Documents/TEE_Project/docs/SERVICENOW_DASHBOARD_GUIDE.md).
3.  **What to Say**: *"This dashboard shows the 15 tickets our AI successfully handled this morning. Let's look at one example..."* (Then open a pre-made ticket).

---

## Technical Troubleshooting Checkboard (Pre-Demo)
1.  **Internet**: Ensure you can reach `dev273008.service-now.com`.
2.  **Environment**: Ensure `.venv` is active and `transformers` is installed.
3.  **Clean Slate**: If doing a live demo, delete old test records from the ServiceNow table before you start.
