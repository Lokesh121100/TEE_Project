#!/usr/bin/env python3
"""
Frontend Element Verification - Checks all required HTML/CSS/JS elements
"""

import re
from pathlib import Path

def check_file_content(filepath, patterns, description):
    """Check if patterns exist in file"""
    print(f"\n{'='*70}")
    print(f"[TEST] {description}")
    print(f"{'='*70}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        all_found = True
        for pattern_name, pattern in patterns.items():
            found = pattern in content
            status = "[OK]" if found else "[FAIL]"
            print(f"{status} {pattern_name}")
            all_found = all_found and found

        if all_found:
            print(f"\n[RESULT] {description}: ALL CHECKS PASSED")
        else:
            print(f"\n[RESULT] {description}: SOME CHECKS FAILED")

        return all_found
    except Exception as e:
        print(f"[ERROR] Could not read file: {e}")
        return False

# Test HTML
html_patterns = {
    "Escalation modal div exists": 'id="escalation-modal"',
    "Escalate button exists": 'id="escalate-btn"',
    "Modal close button exists": 'id="modal-close"',
    "Reason textarea exists": 'id="escalation-reason"',
    "Priority dropdown exists": 'id="escalation-priority"',
    "Transcript display exists": 'id="escalation-transcript"',
    "Modal submit button exists": 'id="modal-submit"',
    "Modal cancel button exists": 'id="modal-cancel"',
    "Escalation actions container exists": 'id="escalation-actions"',
}

# Test CSS
css_patterns = {
    "Button styling (.btn-escalate)": ".btn-escalate {",
    "Modal styling (.modal)": ".modal {",
    "Modal content styling": ".modal-content {",
    "Modal header styling": ".modal-header {",
    "Modal close button styling": ".modal-close {",
    "Modal body styling": ".modal-body {",
    "Modal footer styling": ".modal-footer {",
    "Form group styling": ".form-group {",
    "Button hover state": ".btn-escalate:hover",
}

# Test JavaScript
js_patterns = {
    "Modal element reference": 'document.getElementById("escalation-modal")',
    "Escalate button reference": 'document.getElementById("escalate-btn")',
    "Escalation reason reference": 'document.getElementById("escalation-reason")',
    "Priority dropdown reference": 'document.getElementById("escalation-priority")',
    "Modal open handler": 'escalationBtn.addEventListener("click"',
    "Modal close handler": 'modalClose.addEventListener("click"',
    "Modal submit handler": 'modalSubmit.addEventListener("click"',
    "API endpoint call": 'fetch("/api/escalate"',
    "POST method": 'method: "POST"',
    "Transcript capture": 'transcript: conversationTranscript',
    "Close modal function": 'const closeModal = () => {',
    "Update transcript display": 'const updateTranscriptDisplay = () => {',
}

def main():
    print("\n" + "="*70)
    print("FRONTEND ELEMENT VERIFICATION TEST")
    print("="*70)

    html_path = Path("src/frontend/index.html")
    css_path = Path("src/frontend/styles.css")
    js_path = Path("src/frontend/app.js")

    results = {}

    # Test files exist
    print(f"\n[CHECK] File Existence")
    print(f"  index.html: {'[OK]' if html_path.exists() else '[MISSING]'}")
    print(f"  styles.css: {'[OK]' if css_path.exists() else '[MISSING]'}")
    print(f"  app.js:     {'[OK]' if js_path.exists() else '[MISSING]'}")

    # Test HTML
    results['html'] = check_file_content(str(html_path), html_patterns, "HTML Structure")

    # Test CSS
    results['css'] = check_file_content(str(css_path), css_patterns, "CSS Styling")

    # Test JavaScript
    results['js'] = check_file_content(str(js_path), js_patterns, "JavaScript Logic")

    # Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test.upper()}")

    print(f"\nResults: {passed}/{total} test categories passed")

    if passed == total:
        print("\n[SUCCESS] ALL FRONTEND ELEMENTS VERIFIED")
        print("\nNow test in browser:")
        print("  1. python src/api/app.py")
        print("  2. Open http://localhost:8000")
        print("  3. Submit incident")
        print("  4. Click 'Escalate to Human Support'")
        print("  5. Fill form and submit")
        return 0
    else:
        print("\n[WARNING] Some elements missing - check above for details")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
