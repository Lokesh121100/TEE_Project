# ServiceNow Guide: Creating the AI Impact Dashboard

This guide will help you create a **Professional AI Dashboard** directly inside ServiceNow. This is the best way to show the demo to a client because it looks like a real, finished product.

---

## Step 1: Create the Dashboard
1.  Log in to your ServiceNow instance: `https://dev273008.service-now.com`.
2.  In the Filter Navigator (top left), type **"Dashboards"**.
3.  Click **New** to create a new dashboard.
4.  Name it: **"AI Service Desk Analytics"**.

## Step 2: Add Professional Widgets
Click the **"+" (Add Widgets)** icon on the top right of your dashboard to add these:

### 1. The "Total Impact" Scorecard (Count)
*   **Type**: Data Visualization -> Single Score.
*   **Table**: `x_1941577_tee_se_0_ai_incident_demo`.
*   **Condition**: `Created is Today`.
*   **Title**: "AI-Automated Incidents (Today)".

### 2. The "Intelligence" Gauge (Accuracy)
*   **Type**: Data Visualization -> Gauge.
*   **Table**: `x_1941577_tee_se_0_ai_incident_demo`.
*   **Aggregation**: Average.
*   **Field**: `AI Confidence Score`.
*   **Title**: "Avg AI Confidence Index".

### 3. The "Categorization" Pie Chart
*   **Type**: Data Visualization -> Pie.
*   **Table**: `x_1941577_tee_se_0_ai_incident_demo`.
*   **Group By**: `Category`.
*   **Title**: "AI-Detected Categories".

### 4. The "Live Feed" (Recent Activity)
*   **Type**: List.
*   **Table**: `x_1941577_tee_se_0_ai_incident_demo`.
*   **Columns**: Number, Short Description, Category, Confidence Score.
*   **Sort**: Created (Descending).

---

## Step 3: The "Magic" Moment in the Demo
1.  Keep this Dashboard open in your browser.
2.  Run the AI script (`python src/ai_agent/main.py`).
3.  **Immediately refresh the dashboard.**
4.  Show the client how the numbers go up and the pie chart updates automatically. 

**This proves the system is working in real-time without anyone manually typing!**
