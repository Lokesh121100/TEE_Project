import requests
from requests.auth import HTTPBasicAuth
import json

# Configuration
SERVICENOW_URL = "https://dev273008.service-now.com"
SERVICENOW_USER = "admin"
SERVICENOW_PASS = "@nL=BMhj07Sk"
TABLE_NAME = "x_1941577_tee_se_0_ai_incident_demo"

def increase_field_limit():
    print(f"[*] Attempting to increase limit for {TABLE_NAME}.short_description")
    
    # 1. Find the sys_id of the dictionary entry
    url = f"{SERVICENOW_URL}/api/now/table/sys_dictionary?sysparm_query=name={TABLE_NAME}^element=short_description&sysparm_fields=sys_id"
    
    try:
        response = requests.get(url, auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS))
        if response.status_code == 200:
            results = response.json().get('result', [])
            if not results:
                print("[!] Dictionary entry not found.")
                return
            
            sys_id = results[0]['sys_id']
            print(f"[*] Found Dictionary SysID: {sys_id}")
            
            # 2. Update the max_length
            update_url = f"{SERVICENOW_URL}/api/now/table/sys_dictionary/{sys_id}"
            payload = {"max_length": 4000}
            
            upd_resp = requests.put(
                update_url,
                json=payload,
                auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS),
                headers={"Content-Type": "application/json"}
            )
            
            if upd_resp.status_code in [200, 204]:
                print("✅ Successfully increased Short Description limit to 4000 characters!")
            else:
                print(f"❌ Failed to update limit: {upd_resp.status_code}")
                print(upd_resp.text)
        else:
            print(f"Error finding dictionary: {response.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    increase_field_limit()
