# Quick Frontend Testing Checklist - 5 Minutes

## Prerequisites
- Server running: `python src/api/app.py`
- Browser: http://localhost:8000
- DevTools ready: Press F12

---

## TEST 1: Submit Incident (1 min)

```
1. [ ] Browser shows ARIA home page
2. [ ] Text input field visible: "Describe the incident..."
3. [ ] Type: "Email server down, cannot send messages"
4. [ ] Click blue "Process Incident" button
5. [ ] Processing indicator appears
6. [ ] Result shows with green checkmark
```

**Expected**: Green result box with incident classification

---

## TEST 2: Escalation Button Appears (30 seconds)

```
7. [ ] ORANGE button appears below result
8. [ ] Button text: "Escalate to Human Support"
9. [ ] Button has upward arrow icon
10. [ ] Button is clickable (not grayed out)
```

**If button NOT visible**:
- Open DevTools (F12)
- Check Console for errors
- Check Elements → Search for "escalate-btn"

---

## TEST 3: Open Modal (30 seconds)

```
11. [ ] Click escalation button
12. [ ] Dark modal appears with animation
13. [ ] Modal title: "Escalate to Human Support"
14. [ ] X button visible (top right)
15. [ ] Reason textarea visible and focused
16. [ ] Priority dropdown visible (Medium selected)
17. [ ] Transcript shows (at least "No conversation yet")
18. [ ] Cancel and Submit buttons visible
```

**If modal doesn't appear**:
- Check Console for JavaScript errors
- Try opening DevTools before clicking button

---

## TEST 4: Fill & Submit (1.5 min)

```
19. [ ] Click in reason field
20. [ ] Type: "Customer unable to send critical email, business impact"
21. [ ] Open Priority dropdown
22. [ ] Select: "High"
23. [ ] Verify transcript shows (conversation history)
24. [ ] Click "Submit Escalation" button
25. [ ] Button changes to "Submitting..."
26. [ ] Button becomes disabled
```

**Waiting**: 1-2 seconds for processing

```
27. [ ] Modal closes
28. [ ] Success message appears
29. [ ] Shows: "✓ Escalated Successfully"
30. [ ] Reference Number visible: "ESC-INC-[number]"
31. [ ] Team: "L2 Senior Support"
32. [ ] SLA: "120 minutes"
```

---

## TEST 5: Verify API Call (1 min)

```
33. [ ] Open DevTools (F12)
34. [ ] Go to Network tab
35. [ ] Repeat TEST 4
36. [ ] Look for POST request to "/api/escalate"
37. [ ] Click on request
38. [ ] Check Request Body: should have ticket_id, reason, priority, transcript
39. [ ] Check Response: should have escalation_number, sla_minutes, assigned_team
40. [ ] Response status: 200 OK
```

---

## TEST 6: Error Handling (30 seconds)

```
41. [ ] Click "Escalate to Human Support" again
42. [ ] Leave reason textarea EMPTY
43. [ ] Click "Submit Escalation"
44. [ ] Alert appears: "Please provide a reason for escalation"
45. [ ] Click OK to close alert
46. [ ] Modal still open (didn't submit)
```

---

## TEST 7: Modal Closing (1 min)

```
47. [ ] Type reason: "Test reason"
48. [ ] Press ESC key
49. [ ] Modal closes (should work with keyboard)
50. [ ] Click button again to reopen
51. [ ] Form is cleared (reason empty, priority reset to Medium)
52. [ ] Click X button
53. [ ] Modal closes
54. [ ] Click button again
55. [ ] Click Cancel button
56. [ ] Modal closes
57. [ ] Click button, then click outside modal
58. [ ] Modal closes
```

---

## Quick Scoring

**Count your [OK] checks:**

- **40-58 [OK]**: ✅ Fully Working - Production Ready
- **30-39 [OK]**: ⚠️ Mostly Working - Minor issues
- **20-29 [OK]**: ❌ Has Bugs - Needs fixes
- **<20 [OK]**: ❌ Not Working - Major issues

---

## If Something Fails

### Button Not Appearing
```bash
# Check app.js
grep -n "escalationBtn.addEventListener" src/frontend/app.js

# Check HTML
grep -n 'id="escalate-btn"' src/frontend/index.html

# Check CSS
grep -n ".btn-escalate" src/frontend/styles.css
```

### Modal Not Opening
```bash
# Check JavaScript
grep -n "escalationBtn.addEventListener" src/frontend/app.js

# Open browser console and try:
javascript> document.getElementById("escalation-modal").style.display = "flex"
# Should show modal if it exists
```

### Submit Not Working
```bash
# Check backend
curl -X POST http://localhost:8000/api/escalate \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"TEST","reason":"Test","priority":"High","transcript":[]}'

# Should return 200 with escalation_number
```

### API Not Responding
```bash
# Check server running
# Check for port 8000 conflicts
# Restart: python src/api/app.py
```

---

## Success Criteria

✅ All 58 checks passed = **Escalation Workflow FULLY WORKING**

**Next Steps**:
1. Fix any failing items
2. Test with different incident types
3. Verify escalation creates ServiceNow incident
4. Move to Dashboard building
