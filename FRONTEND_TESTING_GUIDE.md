# Frontend Testing Guide - Escalation Workflow

## Bugs Fixed
1. ✅ Missing null check on modal click listener (could crash if modal not found)
2. ✅ Missing null checks in closeModal() function
3. ✅ Missing null check in updateTranscriptDisplay()

---

## Step-by-Step Frontend Testing

### PART 1: Submit an Incident

**1. Open the browser**
```
http://localhost:8000
```

**2. Look for the incident form**
- You should see:
  - Text input: "Describe the incident or question..."
  - "Clear" button (gray)
  - "Process Incident" button (blue)
  - Quick scenario chips below

**3. Submit an incident**
Choose one:

**Option A: Use quick chip**
- Click any scenario chip (e.g., "Network Connection Lost")
- Text should auto-fill in the input
- Click "Process Incident"

**Option B: Type custom incident**
- Type: `"Email server is not working, users cannot send messages"`
- Click "Process Incident"

**Expected Result:**
- Status changes to "Processing..."
- Reasoning steps appear in log
- Results display with green checkmark
- **Escalate to Human Support button appears** ← CRITICAL

---

### PART 2: Verify Escalation Button

**1. After result is shown, look for the button**

Button should have:
- ✅ Orange gradient color
- ✅ Upward arrow icon
- ✅ Text: "Escalate to Human Support"
- ✅ Located below the result

**If button is NOT visible:**
- Open browser DevTools (F12)
- Go to Console tab
- Check for errors
- Look for the HTML: `<div id="escalation-actions">`

---

### PART 3: Click the Button & Open Modal

**1. Click "Escalate to Human Support" button**

**Expected Result:**
- Modal dialog appears with smooth slide-in animation
- Modal shows:
  - Title: "Escalate to Human Support"
  - X close button (top right)
  - Reason textarea (with placeholder text)
  - Priority dropdown (Medium selected by default)
  - Conversation transcript display
  - Cancel and Submit buttons
- Reason textarea should auto-focus

**If modal doesn't appear:**
```
Press F12 → Console → Check for JavaScript errors
```

---

### PART 4: Fill Form & Submit

**1. Reason Field**
- Type: `"Customer experiencing critical email outage, unable to work"`
- Required: Yes (must not be empty)

**2. Priority Dropdown**
- Open dropdown
- Select: "High" (or "Critical" to test urgency)

**3. Transcript Display**
- Should show: `"User inquiry processed. Result: [incident type]"`
- Displays conversation history automatically

**4. Click Submit Escalation**

**Expected Result:**
- Submit button changes to "Submitting..."
- Button becomes disabled (gray)
- Brief processing delay (1-2 seconds)
- Modal closes
- Success message appears showing:
  - ✓ Escalated Successfully
  - Reference Number: `ESC-INC-[ticket-id]`
  - Assigned Team: L2 Senior Support
  - SLA: 120 minutes response time

---

### PART 5: Verify Success Response

**Success screen should show:**
```
✓ Escalated Successfully
Reference Number: ESC-INC-TICKET-001
Assigned Team: L2 Senior Support
SLA: 120 minutes response time
Successfully escalated to L2 Support. Reference: ESC-INC-TICKET-001
```

---

## Testing Checklist

### Button & Modal
- [ ] Escalation button visible after result
- [ ] Button has orange gradient color
- [ ] Button has arrow icon
- [ ] Clicking button opens modal
- [ ] Modal appears with animation
- [ ] Modal has all required fields

### Form Fields
- [ ] Reason textarea focusable
- [ ] Placeholder text visible
- [ ] Priority dropdown opens
- [ ] All priority options present (Low/Medium/High/Critical)
- [ ] Medium selected by default
- [ ] Transcript displays correctly

### Form Submission
- [ ] Submit button disabled during request
- [ ] Loading state shows "Submitting..."
- [ ] Modal closes on success
- [ ] Success message displays with reference number
- [ ] SLA information shown (120 minutes)
- [ ] Team assignment shown (L2 Senior Support)

### Error Handling
- [ ] Try submitting with empty reason → should show alert
- [ ] Check browser console for any errors
- [ ] Network request should go to `/api/escalate`

### Modal Closing
- [ ] Can close with X button
- [ ] Can close with Cancel button
- [ ] Can close by pressing ESC key
- [ ] Can close by clicking outside modal
- [ ] Form clears on close (reason field empty, priority reset to Medium)

---

## Browser DevTools Debugging

**To monitor the API request:**

1. Press F12 (Open DevTools)
2. Go to Network tab
3. Click "Escalate to Human Support"
4. Fill form and submit
5. Look for POST request to `/api/escalate`
6. Click on it to see:
   - Request headers
   - Request body (should include ticket_id, reason, priority, transcript)
   - Response (should show escalation_number, sla_minutes, assigned_team)

**Expected Response (200 OK):**
```json
{
  "status": "escalated",
  "escalation_number": "ESC-INC-TICKET-001",
  "message": "Successfully escalated to L2 Support. Reference: ESC-INC-TICKET-001",
  "sla_minutes": 120,
  "assigned_team": "L2 Senior Support",
  "transcript_saved": true
}
```

---

## Console Errors to Watch For

### Error 1: "Cannot read property X of null"
```
Means an HTML element wasn't found.
Fix: Check index.html for required IDs:
- escalation-modal
- escalate-btn
- escalation-reason
- escalation-priority
- modal-submit
- modal-cancel
- modal-close
```

### Error 2: "Failed to fetch /api/escalate"
```
Means backend endpoint not responding.
Fix:
1. Verify app.py running
2. Check app.py has @app.post("/api/escalate") endpoint
3. Restart the server
```

### Error 3: Modal appears but form doesn't work
```
Check that form elements have correct IDs in HTML.
Compare index.html line 205-215 with expected element IDs.
```

---

## Quick Test Scenarios

### Scenario 1: Happy Path
1. Submit incident
2. See result
3. Click Escalate
4. Fill form with all fields
5. Submit
6. See success message ✅

### Scenario 2: Error Handling
1. Submit incident
2. Click Escalate
3. Leave reason EMPTY
4. Click Submit
5. Should show alert: "Please provide a reason for escalation" ✅

### Scenario 3: Modal Closing
1. Submit incident
2. Click Escalate (modal opens)
3. Click X button
4. Modal should close ✅

### Scenario 4: Backend Integration
1. Submit incident and escalate
2. Open DevTools Network tab
3. Check POST /api/escalate request
4. Verify response contains escalation_number ✅

---

## If Tests Fail

1. **Check app.py is running**
   ```bash
   python src/api/app.py
   ```

2. **Verify endpoint exists**
   ```bash
   grep -n "@app.post(\"/api/escalate\")" src/api/app.py
   ```

3. **Check HTML elements**
   ```bash
   grep -n "escalation-modal\|escalate-btn" src/frontend/index.html
   ```

4. **Verify CSS styling**
   ```bash
   grep -n ".btn-escalate" src/frontend/styles.css
   ```

5. **Test API directly with curl**
   ```bash
   curl -X POST http://localhost:8000/api/escalate \
     -H "Content-Type: application/json" \
     -d '{
       "ticket_id": "TEST-001",
       "reason": "Testing escalation",
       "priority": "High",
       "transcript": ["Test message"]
     }'
   ```

---

## Success Criteria

✅ All items checked = Escalation workflow fully working
⚠️ Some items failing = Bugs need fixing
❌ No button appearing = Check app.js or HTML

**Status**: Ready for end-to-end user testing
