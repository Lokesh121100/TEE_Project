import requests
from requests.auth import HTTPBasicAuth

# Credentials from hf_demo.py
SN_URL = "https://dev273008.service-now.com"
SN_USER = "admin"
SN_PASS_VAR1 = "a nLBMhj07Sk"
SN_PASS_VAR2 = "anLBMhj07Sk"

def test_connection(password, name):
    url = f"{SN_URL}/api/now/table/sys_user?sysparm_limit=1"
    try:
        r = requests.get(url, auth=HTTPBasicAuth(SN_USER, password), headers={"Accept": "application/json"})
        print(f"Testing {name}: Status {r.status_code}")
        if r.status_code == 200:
            return True
    except Exception as e:
        print(f"Error: {e}")
    return False

if __name__ == "__main__":
    if test_connection(SN_PASS_VAR1, "With Space"):
        print("✓ Success with space!")
    elif test_connection(SN_PASS_VAR2, "No Space"):
        print("✓ Success without space!")
    else:
        print("✗ All attempts failed.")
