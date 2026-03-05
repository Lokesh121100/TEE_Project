# 📊 ServiceNow Dashboard Setup Guide
**For ARIA v2.0 - AI Governance & Accuracy Tracking**

**Status**: CRITICAL WORK ITEM | **Priority**: 🔴 HIGH | **Estimated Time**: 2-3 hours
**Date Created**: March 5, 2026
**Purpose**: Display AI classification accuracy, confidence scores, and incident metrics to evaluators

---

## ✅ Overview

This guide walks you through creating a **ServiceNow Dashboard** that visualizes real-time data from the ARIA AI Incident table. This dashboard demonstrates:
- ✅ AI accuracy metrics (correct vs incorrect classifications)
- ✅ Confidence score distribution (how confident is the AI?)
- ✅ Category performance (which categories does AI handle best?)
- ✅ Auto-resolution rates (how many incidents are auto-resolved?)
- ✅ Incident volume trends (system usage over time)

**Expected Result**: A professional 4-widget dashboard showing governance metrics to TEE evaluators.

---

## 🔧 Step 1: Create a Report from the AI Incident Table

### 1.1 Access ServiceNow Reports
```
URL: https://dev273008.service-now.com
Login: admin / @nL=BMhj07Sk
Navigate: All > Reports
```

### 1.2 Create New Report
1. Click **"New"** → **"New Report"**
2. Choose **Table**: `x_1941577_tee_se_0_ai_incident_demo`
3. Click **"Create Report"**

### 1.3 Add Report Columns
Select these fields to display:
- ✅ **short_description** (Incident summary)
- ✅ **category** (AI classification category)
- ✅ **subcategory** (AI classification subcategory)
- ✅ **ai_confidence_score** (0-100 confidence rating)
- ✅ **status** (New, In Progress, Resolved)
- ✅ **assignment_group** (Which team handles it)
- ✅ **ai_case_summary** (AI-generated summary)
- ✅ **sys_created_on** (When incident was created)

### 1.4 Add Filters (Optional)
- **Filter 1**: `status` is not `Closed`
- **Filter 2**: `ai_confidence_score` is not empty

### 1.5 Save Report
- **Name**: `ARIA AI Incident Accuracy Report`
- **Location**: `Reports > Service Desk`
- **Make Public**: ✅ Yes

---

## 📈 Step 2: Create Dashboard Widgets

### 2.1 Create Dashboard
1. Navigate: **All > Dashboards**
2. Click **"New Dashboard"**
3. **Name**: `ARIA AI Governance Dashboard`
4. **Description**: `Real-time AI classification accuracy and incident metrics`

### 2.2 Widget 1: Accuracy Metrics (Scorecard)

**Purpose**: Shows overall AI accuracy percentage

**Steps**:
1. Click **"Add Widget"** → **"Scorecard"**
2. **Label**: `AI Accuracy`
3. **Metric**: Count of records where:
   - Table: `x_1941577_tee_se_0_ai_incident_demo`
   - Condition: `category` is not empty
4. **Secondary Metric**: Count where `ai_confidence_score` ≥ 85
5. **Display**: Show both numbers (e.g., "8 out of 10")
6. **Color Scheme**: 🟢 Green for >80%, 🟡 Yellow for 60-80%, 🔴 Red for <60%

**Formula for Accuracy %**:
```
(Count of incidents with confidence ≥ 85) / (Total incidents) × 100
```

---

### 2.3 Widget 2: Confidence Distribution (Histogram)

**Purpose**: Shows how many incidents fall into each confidence range

**Steps**:
1. Click **"Add Widget"** → **"Bar Chart"**
2. **Title**: `Confidence Score Distribution`
3. **X-Axis**: Confidence Score Ranges
   - 0-20% (Low Confidence)
   - 21-40% (Below Average)
   - 41-60% (Average)
   - 61-80% (Good)
   - 81-100% (High Confidence)
4. **Y-Axis**: Count of incidents
5. **Metric**: Count `ai_confidence_score` by ranges
6. **Color**: Blue to Green gradient (blue=low, green=high)

**SQL-like Logic**:
```
Count incidents grouped by:
  CASE WHEN ai_confidence_score <= 20 THEN '0-20% (Low)'
       WHEN ai_confidence_score <= 40 THEN '21-40% (Below Avg)'
       WHEN ai_confidence_score <= 60 THEN '41-60% (Average)'
       WHEN ai_confidence_score <= 80 THEN '61-80% (Good)'
       ELSE '81-100% (High)' END
```

---

### 2.4 Widget 3: Category Performance (Pie/Donut Chart)

**Purpose**: Shows which incident categories the AI handles

**Steps**:
1. Click **"Add Widget"** → **"Pie Chart"**
2. **Title**: `Incidents by Category`
3. **Metric**: Count of incidents
4. **Group By**: `category`
5. **Show Labels**: Yes (with percentages)
6. **Legend**: Displayed on right side

**Expected Breakdown**:
- 20% Access (passwords, onboarding)
- 20% Network (VPN, WiFi)
- 20% Hardware (printer, laptop)
- 20% Software (Outlook, Adobe, VDI)
- 20% Other

---

### 2.5 Widget 4: Auto-Resolution Rate (Gauge Chart)

**Purpose**: Shows percentage of incidents auto-resolved by ARIA

**Steps**:
1. Click **"Add Widget"** → **"Gauge"**
2. **Title**: `Auto-Resolution Rate`
3. **Metric**: Count where `status` = "Resolved"
4. **Total**: Count of all incidents
5. **Calculate %**: (Resolved / Total) × 100
6. **Min/Max**: 0% - 100%
7. **Threshold Colors**:
   - 🔴 Red: 0-30%
   - 🟡 Yellow: 31-60%
   - 🟢 Green: 61-100%

---

### 2.6 Widget 5: Incident Trend (Optional - Line Chart)

**Purpose**: Shows incident volume over time

**Steps**:
1. Click **"Add Widget"** → **"Line Chart"**
2. **Title**: `Incident Volume Trend`
3. **X-Axis**: `sys_created_on` (by Day or by Hour)
4. **Y-Axis**: Count of incidents
5. **Data Grouping**: Aggregate by hour/day
6. **Show Data Points**: Yes

---

## 🎨 Step 3: Design Dashboard Layout

### Recommended Layout (2x2 + Footer)
```
┌─────────────────────┬─────────────────────┐
│  Accuracy Metrics   │ Confidence Distrib  │
│   (Scorecard)       │   (Bar Chart)       │
├─────────────────────┼─────────────────────┤
│  Category Perform   │ Auto-Resolution     │
│   (Pie Chart)       │  (Gauge Chart)      │
├─────────────────────────────────────────┤
│          Incident Volume Trend          │
│            (Line Chart)                 │
└─────────────────────────────────────────┘
```

### Widget Sizing
- **Top Row**: 50% width each (Accuracy + Confidence)
- **Middle Row**: 50% width each (Categories + Auto-Resolution)
- **Bottom Row**: 100% width (Trend line)

### Colors & Theme
- **Primary Color**: Dark Blue (#0066CC)
- **Accent Color**: Neon Green (#00CC66)
- **Background**: Light Gray (#F5F5F5)
- **Text**: Dark Gray (#333333)

---

## 📊 Step 4: Configure Data Refresh

### Auto-Refresh Settings
1. Dashboard **Settings** → **Refresh Interval**
2. Set to **"Every 5 minutes"**
3. This keeps metrics live during the demo

### Live Data Updates
- As test scenarios run, incidents are created in ServiceNow
- Dashboard automatically pulls and displays the latest data
- Evaluators see real-time accuracy metrics updating

---

## 🧪 Step 5: Validate Dashboard with Test Data

### 5.1 Run Demo Scenarios
```bash
# Terminal 1: Start demo API
python src/api/app_demo.py

# Terminal 2: Run scenario tests
python test_demo_scenarios.py
```

### 5.2 Check Dashboard Updates
1. Open dashboard in browser
2. Observe metrics updating as incidents are created
3. Verify:
   - ✅ Accuracy percentage increases
   - ✅ Confidence distribution shows incidents in each range
   - ✅ Category breakdown matches scenario mix
   - ✅ Auto-resolution rate shows resolved incidents

---

## 🎯 Step 6: Demo Flow for Evaluators

### During TEE Demo (10 minutes)
1. **Minute 1-2**: Show dashboard overview ("Here's real-time AI governance")
2. **Minute 3-5**: Run first 5 scenarios live
   - Dashboard updates automatically
   - Point out accuracy metrics improving
3. **Minute 6-8**: Run remaining 5 scenarios
   - Show final accuracy percentage
   - Highlight confidence distribution
4. **Minute 9-10**: Q&A
   - "How do you ensure AI accuracy?" → Point to confidence thresholds
   - "What's your escalation rate?" → Show auto-resolution gauge
   - "How do you handle different types of incidents?" → Show category breakdown

---

## 📋 Checklist Before Demo

- [ ] Dashboard created in ServiceNow
- [ ] All 5 widgets configured and displaying data
- [ ] Auto-refresh enabled (5-minute intervals)
- [ ] Test data loaded (run scenario tests)
- [ ] Dashboard metrics showing correctly
- [ ] Colors and layout are professional
- [ ] Mobile/tablet responsive tested
- [ ] Demo URL bookmarked and ready
- [ ] Backup screenshot taken (in case of tech issues)

---

## 🔗 Quick Reference: Field Mapping

| Dashboard Widget | ServiceNow Field | Type | Example |
|---|---|---|---|
| Accuracy % | `ai_confidence_score` | Number | 85% |
| Confidence Range | `ai_confidence_score` | Number Range | 0-100 |
| Category | `category` | Dropdown | access, network, hardware, software |
| Subcategory | `subcategory` | Text | Password, VPN, Printer, Email |
| Status | `status` | Dropdown | New, In Progress, Resolved |
| Team | `assignment_group` | Lookup | Service Desk, Network Support, etc. |
| Summary | `ai_case_summary` | Text | "Password reset required..." |
| Created Date | `sys_created_on` | DateTime | 2026-03-05 14:30:00 |

---

## 🆘 Troubleshooting

### Issue: Widgets show "No Data"
**Solution**:
- Verify incidents exist in ServiceNow table
- Run `python test_demo_scenarios.py` to populate test data
- Check dashboard filters (may be filtering out all incidents)
- Refresh browser page (F5)

### Issue: Confidence scores all show 0
**Solution**:
- Check `ai_confidence_score` field is being populated
- Verify API is calculating confidence correctly
- Run demo test with verbose output to debug

### Issue: Dashboard slow or lagging
**Solution**:
- Reduce data range (show last 24 hours only)
- Increase refresh interval to 10-15 minutes
- Optimize widgets (use aggregates instead of row-by-row data)

### Issue: Charts not displaying correctly
**Solution**:
- Delete widget and recreate it
- Verify field types are correct (numbers for metrics, text for grouping)
- Try different chart type (bar instead of pie, etc.)

---

## 📈 Expected Results

After completing this setup, you should have:

✅ **Accuracy Scorecard**: Shows 80-100% accuracy (based on confidence thresholds)
✅ **Confidence Histogram**: Shows most incidents in 81-100% range
✅ **Category Pie Chart**: Shows balanced distribution across 5 incident types
✅ **Auto-Resolution Gauge**: Shows 60-80% of incidents resolved without escalation
✅ **Trend Line**: Shows incident volume over time as demo runs

**Impact**: Evaluators see AI governance in action - real-time metrics proving the system works.

---

## ⏱️ Time Estimate
- **Setup & Configuration**: 1.5 hours
- **Testing & Validation**: 0.5 hours
- **Polish & Refinement**: 1 hour
- **Total**: 2-3 hours

---

**Next Steps After Dashboard**:
1. ✅ Dashboard (THIS) - 2-3 hours
2. Create Presentation Slides - 2-3 hours
3. Add Human Handover Workflow - 3-4 hours
4. Prepare Q&A Guide - 1-2 hours

**Total for TEE-Ready**: 8-12 hours
