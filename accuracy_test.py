import sys
import os
import json
import time

# Ensure src/ai_agent is in the path
sys.path.append(os.path.join(os.getcwd(), 'src', 'ai_agent'))

try:
    from poll_servicenow import intelligent_classification
    from main import is_escalation_needed
except ImportError as e:
    print(f"Error: Could not import TEE core modules. {e}")
    sys.exit(1)

test_cases = [
    # 1. Access/Password
    {"msg": "I forgot my password", "cat": "access", "sub": "Password"},
    {"msg": "My account is locked", "cat": "access", "sub": "Password"},
    {"msg": "I cannot log in", "cat": "access", "sub": "Password"},
    {"msg": "Password not working", "cat": "access", "sub": "Password"},
    {"msg": "Need to reset my credentials", "cat": "access", "sub": "Password"},
    # 2. Network/VPN
    {"msg": "VPN not connecting", "cat": "network", "sub": "VPN"},
    {"msg": "VPN keeps dropping", "cat": "network", "sub": "VPN"},
    {"msg": "Cannot access company network", "cat": "network", "sub": "VPN"},
    {"msg": "Remote access broken", "cat": "network", "sub": "VPN"},
    {"msg": "VPN error on my laptop", "cat": "network", "sub": "VPN"},
    # 3. Hardware/Performance
    {"msg": "My laptop is really slow", "cat": "hardware", "sub": "Performance"},
    {"msg": "Computer takes ages to start", "cat": "hardware", "sub": "Performance"},
    {"msg": "Everything is freezing", "cat": "hardware", "sub": "Performance"},
    {"msg": "High CPU usage", "cat": "hardware", "sub": "Performance"},
    {"msg": "Device performance is terrible", "cat": "hardware", "sub": "Performance"},
    # 4. Software/Email
    {"msg": "Outlook keeps crashing", "cat": "software", "sub": "Email"},
    {"msg": "Attachments won't open in email", "cat": "software", "sub": "Email"},
    {"msg": "Outlook is frozen", "cat": "software", "sub": "Email"},
    {"msg": "Cannot send emails", "cat": "software", "sub": "Email"},
    {"msg": "Outlook error code 0x800", "cat": "software", "sub": "Email"},
    # 5. Network/VDI
    {"msg": "VDI session disconnects", "cat": "network", "sub": "VDI"},
    {"msg": "Virtual desktop is laggy", "cat": "network", "sub": "VDI"},
    {"msg": "Cannot log into VDI", "cat": "network", "sub": "VDI"},
    {"msg": "Remote desktop session lost", "cat": "network", "sub": "VDI"},
    {"msg": "VDI error every 10 mins", "cat": "network", "sub": "VDI"},
    # 6. Software/Install
    {"msg": "Need Adobe Acrobat installed", "cat": "software", "sub": "Install"},
    {"msg": "Requesting new software", "cat": "software", "sub": "Install"},
    {"msg": "Permission to install app", "cat": "software", "sub": "Install"},
    {"msg": "Need Excel licensed", "cat": "software", "sub": "Software"},
    {"msg": "Install Chrome for me", "cat": "software", "sub": "Install"},
    # 7. Hardware/Printer
    {"msg": "Printer is jammed", "cat": "hardware", "sub": "Printer"},
    {"msg": "Printer offline Floor 3", "cat": "hardware", "sub": "Printer"},
    {"msg": "Error 50.1 on printer", "cat": "hardware", "sub": "Printer"},
    {"msg": "Scanner not working", "cat": "hardware", "sub": "Printer"},
    {"msg": "Printer won't print", "cat": "hardware", "sub": "Printer"},
    # 8. Network/WiFi
    {"msg": "WiFi not visible", "cat": "network", "sub": "WiFi"},
    {"msg": "Cannot see guest wifi", "cat": "network", "sub": "WiFi"},
    {"msg": "WiFi cuts out on phone", "cat": "network", "sub": "WiFi"},
    {"msg": "Corporate WiFi missing", "cat": "network", "sub": "WiFi"},
    {"msg": "Network signal is weak", "cat": "network", "sub": "WiFi"},
    # 9. Hardware/Replacement
    {"msg": "Cracked screen", "cat": "hardware", "sub": "Replacement"},
    {"msg": "Spilled water on laptop", "cat": "hardware", "sub": "Replacement"},
    {"msg": "I was at a party and poured some drink over the laptop", "cat": "hardware", "sub": "Replacement"},
    {"msg": "Broken laptop hinge", "cat": "hardware", "sub": "Replacement"},
    {"msg": "Need a new device", "cat": "hardware", "sub": "Replacement"},
    # 10. Access/Onboarding
    {"msg": "I am a new staff member starting on Monday", "cat": "access", "sub": "Onboarding"},
    {"msg": "Onboarding process help", "cat": "access", "sub": "Onboarding"},
    {"msg": "No laptop for my start date", "cat": "access", "sub": "Onboarding"},
    {"msg": "Manager needs to onboard user", "cat": "access", "sub": "Onboarding"},
    {"msg": "Provisioning for new joiner", "cat": "access", "sub": "Onboarding"},
]

def run_accuracy_test():
    print("=" * 70)
    print("🔬 TEE AI ACCURACY BENCHMARK (50 SAMPLES)")
    print("=" * 70)
    
    passed = 0
    total = len(test_cases)
    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"[{i}/{total}] Testing: \"{test['msg']}\"...", end=" ", flush=True)
        
        # Run classification
        try:
            cat, sub, grp, conf = intelligent_classification(test['msg'])
            
            # Check if correct (case-insensitive for safety)
            is_correct = (cat.lower() == test['cat'].lower())
            
            # Check for forced escalation logic consistency
            esc, _ = is_escalation_needed(test['msg'])
            
            if is_correct:
                passed += 1
                print("✅ PASS")
            else:
                print(f"❌ FAIL (Got: {cat})")
                
            results.append({
                "message": test['msg'],
                "expected_cat": test['cat'],
                "actual_cat": cat,
                "actual_sub": sub,
                "confidence": conf,
                "correct": is_correct,
                "escalated": esc
            })
        except Exception as e:
            print(f"🚨 ERROR: {e}")
            results.append({"message": test['msg'], "error": str(e)})
        
        # Small delay to not overwhelm local Ollama
        time.sleep(0.5)

    accuracy = (passed / total) * 100
    print("\n" + "=" * 70)
    print(f"📊 FINAL ACCURACY: {accuracy:.1f}% ({passed}/{total})")
    print(f"🎯 TARGET: 90.0%")
    print("=" * 70)

    # Save to report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "accuracy": accuracy,
        "passed": passed,
        "total": total,
        "details": results
    }
    
    with open("data/accuracy_report.json", "w") as f:
        json.dump(report, f, indent=4)
    print("\nFull report saved to 'data/accuracy_report.json'")

if __name__ == "__main__":
    run_accuracy_test()
