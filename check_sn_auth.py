import requests
from requests.auth import HTTPBasicAuth

# Credentials from hf_demo.py
SN_URL = "https://dev273008.service-now.com"
SN_USER = "admin"
SN_PASS = "a nLBMhj07Sk"

def test_connection():
    url = f"{SN_URL}/api/now/table/sys_user?sysparm_limit=1"
    try:
        r = requests.get(url, auth=HTTPBasicAuth(SN_USER, SN_PASS), headers={"Accept": "application/json"})
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("✓ Success! Credentials are valid.")
        else:
            print(f"✗ Failed: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
