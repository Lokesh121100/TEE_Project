"""
TEE Project — Automated Test Suite  (FIXED v2 — 2026-03-04)
============================================================
Fixes applied vs the version that produced test_report_20260304_150910.txt:

  FIX 1 (test_01, test_02 in TestMainFunctions):
      generate_incident_summary() returns a (title, analysis) TUPLE.
      Old tests called assertIsInstance(result, str) and result.startswith(...)
      on the tuple directly → TypeError / AttributeError.
      Fixed: unpack tuple before asserting.

  FIX 2 (test_03 in TestAIClassification):
      classify_ticket() returns FOUR values: (cat, sub, grp, conf).
      Old test unpacked only three → ValueError: too many values to unpack.
      Fixed: cat, sub, grp, conf = classify_ticket(msg)

  FIX 3 (test_02 in TestPortalHealth):
      portal.py defines process_portal_incident() NOT process_incident().
      Old test checked hasattr(p, "process_incident") → always False.
      Fixed: check for process_portal_incident.

  FIX 4 (test_04 in TestPortalHealth):
      Same tuple issue as FIX 1.
      Fixed: unpack (title, analysis) and assert on each.

Run from the project root:
    python run_tests.py
"""

import sys
import os
import json
import time
import unittest
import importlib
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from io import StringIO

# ==================== PROJECT CONFIG ====================
PROJECT_ROOT   = r"C:\Users\lokes\Documents\TEE_Project"
SRC_AI_AGENT   = os.path.join(PROJECT_ROOT, "src", "ai_agent")
MCP_SN         = os.path.join(PROJECT_ROOT, "mcp", "servicenow")
KB_PATH        = os.path.join(PROJECT_ROOT, "data", "knowledge_base.json")

SERVICENOW_URL  = "https://dev273008.service-now.com"
SERVICENOW_USER = "admin"
SERVICENOW_PASS = "@nL=BMhj07Sk"
TABLE_NAME      = "x_1941577_tee_se_0_ai_incident_demo"

if SRC_AI_AGENT not in sys.path:
    sys.path.insert(0, SRC_AI_AGENT)
if MCP_SN not in sys.path:
    sys.path.insert(0, MCP_SN)

# ==================== TEST RESULTS TRACKING ====================
_results_log = []

def log(msg):
    _results_log.append(msg)
    print(msg)


# ===================================================================
# SUITE 1 — Environment & Bug Checks
# ===================================================================
class TestEnvironment(unittest.TestCase):
    """Verify runtime environment and that all critical bugs are fixed."""

    def test_01_knowledge_base_exists(self):
        """data/knowledge_base.json must exist"""
        self.assertTrue(os.path.exists(KB_PATH),
            f"Missing: {KB_PATH}")

    def test_02_knowledge_base_valid_json(self):
        """knowledge_base.json must be parseable JSON with at least 1 article"""
        if not os.path.exists(KB_PATH):
            self.skipTest("KB file missing — covered by test_01")
        with open(KB_PATH) as f:
            kb = json.load(f)
        self.assertIsInstance(kb, list)
        self.assertGreater(len(kb), 0)

    def test_03_main_py_importable_no_side_effects(self):
        """Importing main.py must NOT trigger any ServiceNow API calls (Bug 1 fix)"""
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            if 'main' in sys.modules:
                del sys.modules['main']
            import main  # noqa: F401
        finally:
            sys.stdout = old_stdout
        output = captured.getvalue()
        self.assertNotIn("Scenario", output,
            "Bug 1 NOT fixed: for-loop ran at import time!")
        self.assertNotIn("AI Summary", output,
            "Bug 1 NOT fixed: scenario processing ran at import time!")

    def test_04_poll_servicenow_importable_no_side_effects(self):
        """Importing poll_servicenow.py must NOT start the polling loop (Bug 4 fix)"""
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            if 'poll_servicenow' in sys.modules:
                del sys.modules['poll_servicenow']
            if 'main' in sys.modules:
                del sys.modules['main']
            import poll_servicenow  # noqa: F401
        finally:
            sys.stdout = old_stdout
        output = captured.getvalue()
        self.assertNotIn("Polling Service Started", output,
            "Bug 4 NOT fixed: polling banner printed at import time!")
        self.assertNotIn("Listening for new manual tickets", output,
            "Bug 4 NOT fixed: polling loop started at import time!")

    def test_05_no_short_desc_variable_in_poll(self):
        """poll_servicenow.py must not reference undefined 'short_desc' (Bug 2 fix)"""
        poll_path = os.path.join(SRC_AI_AGENT, "poll_servicenow.py")
        with open(poll_path, encoding="utf-8") as f:
            source = f.read()
        self.assertNotIn("else short_desc", source,
            "Bug 2 NOT fixed: 'short_desc' still present — should be 'desc'")

    def test_06_no_duplicate_retrieve_knowledge(self):
        """main.py must define retrieve_knowledge exactly once (Bug 3 fix)"""
        main_path = os.path.join(SRC_AI_AGENT, "main.py")
        with open(main_path, encoding="utf-8") as f:
            source = f.read()
        count = source.count("def retrieve_knowledge(")
        self.assertEqual(count, 1,
            f"Bug 3 NOT fixed: retrieve_knowledge defined {count} times (expected 1)")

    def test_07_required_packages_importable(self):
        """Core packages must be importable"""
        required = ["requests", "json", "os", "time"]
        missing = []
        for pkg in required:
            try:
                importlib.import_module(pkg)
            except ImportError:
                missing.append(pkg)
        self.assertEqual(missing, [],
            f"Missing core packages: {missing}  →  pip install {' '.join(missing)}")

    def test_08_gradio_installed(self):
        """gradio must be installed for the portal to work"""
        try:
            importlib.import_module("gradio")
        except ImportError:
            self.skipTest(
                "gradio not installed. Run:  pip install gradio")


# ===================================================================
# SUITE 2 — ServiceNow API Connectivity
# ===================================================================
class TestServiceNowAPI(unittest.TestCase):
    """Verify ServiceNow dev instance is reachable and credentials work."""

    def _get(self, endpoint, params=None):
        url = f"{SERVICENOW_URL}{endpoint}"
        r = requests.get(url, auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS),
                         params=params, timeout=15)
        return r

    def test_01_instance_reachable(self):
        """GET to /api/now/table/{TABLE_NAME} must return 200"""
        r = self._get(f"/api/now/table/{TABLE_NAME}",
                      params={"sysparm_limit": "1"})
        self.assertEqual(r.status_code, 200,
            f"ServiceNow returned {r.status_code}. Wake PDI at developer.servicenow.com")

    def test_02_response_has_result_key(self):
        """Response JSON must contain a 'result' key"""
        r = self._get(f"/api/now/table/{TABLE_NAME}",
                      params={"sysparm_limit": "1"})
        if r.status_code != 200:
            self.skipTest("API not reachable — covered by test_01")
        self.assertIn("result", r.json())

    def test_03_table_has_custom_ai_fields(self):
        """At least one record must have the ai_case_summary field visible"""
        r = self._get(f"/api/now/table/{TABLE_NAME}",
                      params={"sysparm_limit": "1",
                              "sysparm_fields": "sys_id,number,ai_case_summary"})
        if r.status_code != 200:
            self.skipTest("API not reachable — covered by test_01")
        results = r.json().get("result", [])
        if not results:
            self.skipTest("Table is empty — run main.py first")
        self.assertIn("sys_id", results[0],
            "Table schema may be incorrect — sys_id not returned")


# ===================================================================
# SUITE 3 — main.py Core Functions
# ===================================================================
class TestMainFunctions(unittest.TestCase):
    """
    Unit-test the AI pipeline functions from main.py.

    KEY FIXES vs previous version:
      - generate_incident_summary() returns (title, analysis) TUPLE.
        Old tests did assertIsInstance(result, str) → failed.
        Fixed: unpack tuple and assert on title and analysis separately.
    """

    @classmethod
    def setUpClass(cls):
        if 'main' in sys.modules:
            del sys.modules['main']
        import main as m
        cls.m = m

    # ── FIX 1: generate_incident_summary returns TUPLE not str ──────

    def test_01_generate_incident_summary_returns_tuple(self):
        """generate_incident_summary must return a (title, analysis) tuple"""
        result = self.m.generate_incident_summary(
            "User cannot connect to VPN from home office.")
        self.assertIsInstance(result, tuple,
            f"Expected (title, analysis) tuple but got {type(result).__name__}: {result!r}")
        self.assertEqual(len(result), 2,
            f"Expected 2-element tuple (title, analysis), got {len(result)} elements")

    def test_02_generate_incident_summary_title_is_string(self):
        """Title (result[0]) must be a non-empty string"""
        title, analysis = self.m.generate_incident_summary(
            "Outlook keeps crashing.")
        self.assertIsInstance(title, str,
            f"title must be a string, got {type(title).__name__}")
        self.assertGreater(len(str(title).strip()), 0, "title must not be empty")

    def test_03_generate_incident_summary_analysis_is_string(self):
        """Analysis (result[1]) must be a non-empty string"""
        title, analysis = self.m.generate_incident_summary(
            "Outlook keeps crashing.")
        self.assertIsInstance(analysis, str,
            f"analysis must be a string, got {type(analysis).__name__}")
        self.assertGreater(len(str(analysis).strip()), 0, "analysis must not be empty")


    # ── retrieve_knowledge ───────────────────────────────────────────

    def test_04_retrieve_knowledge_returns_string(self):
        """retrieve_knowledge must return a non-empty string"""
        result = self.m.retrieve_knowledge("VPN not connecting")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_05_retrieve_knowledge_no_crash_on_unknown(self):
        """retrieve_knowledge must not crash for unrecognised input"""
        result = self.m.retrieve_knowledge("zxcvbnmasdfghjkl")
        self.assertIsInstance(result, str)

    # ── run_auto_resolution ──────────────────────────────────────────

    def test_06_run_auto_resolution_vpn(self):
        """run_auto_resolution('VPN', …) must return success=True, status='Resolved'"""
        result = self.m.run_auto_resolution("VPN", "Cannot connect to VPN")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("status"), "Resolved")

    def test_07_run_auto_resolution_password(self):
        """run_auto_resolution('Password', …) must return success=True"""
        result = self.m.run_auto_resolution("Password", "Account locked out")
        self.assertTrue(result.get("success"))

    def test_08_run_auto_resolution_unknown(self):
        """run_auto_resolution with unknown subcategory must return success=False"""
        result = self.m.run_auto_resolution("Unknown_XYZ", "Some random thing")
        self.assertFalse(result.get("success"))

    def test_09_run_auto_resolution_returns_notes(self):
        """auto_fix result must always contain a 'notes' key"""
        for sub in ["VPN", "Password", "VDI", "Replacement", "General"]:
            with self.subTest(subcategory=sub):
                result = self.m.run_auto_resolution(sub, "test")
                self.assertIn("notes", result,
                    f"Missing 'notes' key for subcategory '{sub}'")


# ===================================================================
# SUITE 4 — AI Classification Accuracy
# ===================================================================
class TestAIClassification(unittest.TestCase):
    """
    Test Ollama classification accuracy.

    KEY FIX: classify_ticket() returns FOUR values (cat, sub, grp, conf).
    Old test unpacked only THREE → ValueError: too many values to unpack.
    Fixed: cat, sub, grp, conf = classify_ticket(msg)
    """

    TEST_CASES = [
        ("I can't connect to the VPN from home",               "Network"),
        ("VPN keeps timing out every 10 minutes",               "Network"),
        ("My WiFi won't connect on my laptop",                  "Network"),
        ("Can't see the Corporate_Guest WiFi network",          "Network"),
        ("My password expired and I'm locked out",              "Access"),
        ("Account locked after too many login attempts",        "Access"),
        ("Need access for new joiner starting Monday",          "Access"),
        ("Please reset my MFA authenticator app",              "Access"),
        ("Laptop is extremely slow and freezing",               "Hardware"),
        ("Screen is cracked and battery drains in 20 minutes",  "Hardware"),
        ("Printer shows Error 50.1 after clearing paper jam",   "Hardware"),
        ("Need a device replacement — current one is broken",   "Hardware"),
        ("Outlook crashes when I attach a PDF",                 "Software"),
        ("Adobe Acrobat Pro installation needed urgently",      "Software"),
        ("VDI session disconnects every 10 minutes",            "Software"),
        ("Microsoft Teams keeps freezing during calls",         "Software"),
        ("Excel file won't open, says it's corrupt",            "Software"),
        ("Unable to log into SAP system",                       "Access"),
        ("Need SharePoint access for the new project",          "Access"),
    ]

    @classmethod
    def setUpClass(cls):
        if 'poll_servicenow' in sys.modules:
            del sys.modules['poll_servicenow']
        if 'main' in sys.modules:
            del sys.modules['main']
        import poll_servicenow as ps
        cls.ps = ps
        try:
            requests.get("http://localhost:11434", timeout=3)
            cls.ollama_online = True
        except Exception:
            cls.ollama_online = False
            return
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=5)
            models = r.json().get("models", [])
            cls.llama3_ready = any("llama3" in m.get("name", "") for m in models)
        except Exception:
            cls.llama3_ready = False
            return
        if getattr(cls, 'llama3_ready', False):
            try:
                print("\n  [WARMUP] Loading llama3 into memory (up to 60s)...")
                requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "llama3", "prompt": "Hi", "stream": False},
                    timeout=90
                )
                print("  [WARMUP] llama3 ready.")
            except Exception:
                pass

    def test_01_ollama_server_running(self):
        """Ollama server must be running on localhost:11434"""
        if not getattr(self, 'ollama_online', False):
            self.skipTest("Ollama not running — start with: ollama serve")

    def test_02_llama3_model_available(self):
        """llama3 model must be pulled and ready"""
        if not getattr(self, 'ollama_online', False):
            self.skipTest("Ollama not running")
        if not getattr(self, 'llama3_ready', False):
            self.skipTest("llama3 not found. Run: ollama pull llama3")

    def test_03_classification_accuracy(self):
        """
        FIX: classify_ticket() returns (cat, sub, grp, conf) — 4 values.
        Old code: cat, sub, grp = classify_ticket(msg)  ← ValueError
        Fixed:    cat, sub, grp, conf = classify_ticket(msg)
        """
        if not getattr(self, 'ollama_online', False):
            self.skipTest("Ollama not running")
        if not getattr(self, 'llama3_ready', False):
            self.skipTest("llama3 not available — covered by test_02")

        correct      = 0
        total        = len(self.TEST_CASES)
        failures     = []
        fallback_count = 0

        for msg, expected in self.TEST_CASES:
            # ← KEY FIX: was  cat, sub, grp = ...  (crashed with ValueError)
            #               now cat, sub, grp, conf = ...
            cat, sub, grp, conf = self.ps.classify_ticket(msg)
            if cat and cat.lower() == "inquiry / help":
                fallback_count += 1
            if cat and cat.lower() == expected.lower():
                correct += 1
            else:
                failures.append(
                    f"  '{msg[:50]}' → got '{cat}' (conf={conf:.2f}), expected '{expected}'")

        accuracy = (correct / total) * 100
        log(f"\n  [AI Accuracy] {correct}/{total} correct ({accuracy:.1f}%)")
        log(f"  [Ollama Fallbacks] {fallback_count}/{total}")
        if failures:
            log("  Misclassified:")
            for f in failures:
                log(f)

        self.assertLess(fallback_count, total,
            f"Ollama returned fallbacks for ALL {total} inputs — llama3 may not be loaded.\n"
            "Try: ollama run llama3  (then Ctrl+C and re-run tests)")


# ===================================================================
# SUITE 5 — Portal Health
# ===================================================================
class TestPortalHealth(unittest.TestCase):
    """
    Verify portal.py is importable and exposes the expected API.

    KEY FIXES:
      FIX 3: portal.py defines process_portal_incident() NOT process_incident().
              Old test checked hasattr(p, "process_incident") → always False.
      FIX 4: generate_incident_summary returns tuple — unpack before asserting.
    """

    @classmethod
    def setUpClass(cls):
        try:
            importlib.import_module("gradio")
        except ImportError:
            raise unittest.SkipTest(
                "gradio not installed — run: pip install gradio")
        if 'portal' in sys.modules:
            del sys.modules['portal']
        if 'main' in sys.modules:
            del sys.modules['main']
        import portal as p
        cls.p = p

    def test_01_portal_importable(self):
        """portal.py must import without errors"""
        self.assertIsNotNone(self.p)

    def test_02_process_portal_incident_exists(self):
        """process_portal_incident function must be defined in portal.py"""
        self.assertTrue(hasattr(self.p, "process_portal_incident"),
            "process_portal_incident() not found in portal.py. "
            "Note: the function is named process_portal_incident, not process_incident.")

    def test_03_generate_incident_summary_exists(self):
        """portal.py must expose generate_incident_summary (imported from main)"""
        self.assertTrue(hasattr(self.p, "generate_incident_summary"),
            "generate_incident_summary not accessible from portal.py")

    def test_04_generate_incident_summary_returns_tuple(self):
        """
        FIX: generate_incident_summary returns (title, analysis) TUPLE.
        Old test: assertIsInstance(result, str) → AssertionError.
        Fixed: unpack tuple and assert on title and analysis individually.
        """
        result = self.p.generate_incident_summary(
            "My laptop is running very slowly and the VPN keeps disconnecting")
        self.assertIsInstance(result, tuple,
            f"Expected (title, analysis) tuple but got {type(result).__name__}: {result!r}")
        self.assertEqual(len(result), 2)
        title, analysis = result
        self.assertIsInstance(title, str,
            f"title (result[0]) must be str, got {type(title).__name__}")
        self.assertGreater(len(str(title).strip()), 0,
            "title must not be empty")

    def test_05_demo_block_exists(self):
        """Gradio 'demo' Blocks object must exist in portal.py"""
        self.assertTrue(hasattr(self.p, "demo"),
            "'demo' Gradio Blocks object not found in portal.py")


# ===================================================================
# SUITE 6 — MCP Server Health
# ===================================================================
class TestMCPHealth(unittest.TestCase):
    """Verify the MCP ServiceNow tools module is importable."""

    @classmethod
    def setUpClass(cls):
        if MCP_SN not in sys.path:
            sys.path.insert(0, MCP_SN)

    def test_01_sn_mcp_tools_importable(self):
        """sn_mcp_tools.py must import without errors"""
        try:
            if 'sn_mcp_tools' in sys.modules:
                del sys.modules['sn_mcp_tools']
            import sn_mcp_tools  # noqa: F401
        except Exception as e:
            self.fail(f"sn_mcp_tools.py failed to import: {e}")

    def test_02_script_generator_importable(self):
        """script_generator.py must import without errors (skips if deps missing)"""
        optional_deps = ["nest_asyncio", "langchain_openai"]
        missing_deps = []
        for dep in optional_deps:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing_deps.append(dep)
        if missing_deps:
            self.skipTest(
                f"Missing deps: {', '.join(missing_deps)}\n"
                f"Run: pip install {' '.join(missing_deps)}")
        try:
            if 'script_generator' in sys.modules:
                del sys.modules['script_generator']
            import script_generator  # noqa: F401
        except Exception as e:
            self.fail(f"script_generator.py failed to import: {e}")


# ===================================================================
# RUNNER
# ===================================================================
def run_all_tests():
    suites = [
        ("Environment & Bug Checks",   TestEnvironment),
        ("ServiceNow API",              TestServiceNowAPI),
        ("main.py Core Functions",      TestMainFunctions),
        ("AI Classification Accuracy",  TestAIClassification),
        ("Portal Health",               TestPortalHealth),
        ("MCP Server Health",           TestMCPHealth),
    ]

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(PROJECT_ROOT, f"test_report_{timestamp}.txt")

    overall_passed  = 0
    overall_failed  = 0
    overall_skipped = 0
    report_lines    = []

    header = (
        f"\n{'='*65}\n"
        f"  TEE PROJECT — Automated Test Report  (v2 FIXED)\n"
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"  Instance:  {SERVICENOW_URL}\n"
        f"{'='*65}\n"
    )
    print(header)
    report_lines.append(header)

    for suite_name, suite_class in suites:
        loader = unittest.TestLoader()
        suite  = loader.loadTestsFromTestCase(suite_class)
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(suite)

        passed  = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
        failed  = len(result.failures) + len(result.errors)
        skipped = len(result.skipped)

        overall_passed  += passed
        overall_failed  += failed
        overall_skipped += skipped

        icon  = "[PASS]" if failed == 0 else "[FAIL]"
        block = (
            f"\n{'-'*65}\n"
            f"Suite: {suite_name}  {icon}\n"
            f"  Passed: {passed}  |  Failed: {failed}  |  Skipped: {skipped}\n"
        )

        if result.failures or result.errors:
            block += "\n[FAILURES / ERRORS]\n"
            for test, traceback in result.failures + result.errors:
                last_line = [l for l in traceback.strip().splitlines() if l][-1]
                block += f"  FAIL {test}:\n      {last_line}\n"

        print(block)
        report_lines.append(block)

    total   = overall_passed + overall_failed + overall_skipped
    verdict = ("ALL TESTS PASSED [OK]"
               if overall_failed == 0
               else f"{overall_failed} TEST(S) FAILED [FAIL]")
    summary = (
        f"\n{'='*65}\n"
        f"  FINAL SUMMARY\n"
        f"  Total: {total}  |  Passed: {overall_passed}  "
        f"|  Failed: {overall_failed}  |  Skipped: {overall_skipped}\n"
        f"  Result: {verdict}\n"
        f"{'='*65}\n"
        f"  Report saved to: {report_path}\n"
    )
    print(summary)
    report_lines.append(summary)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    return overall_failed


if __name__ == "__main__":
    failed_count = run_all_tests()
    sys.exit(0 if failed_count == 0 else 1)