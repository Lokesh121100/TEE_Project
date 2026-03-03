import requests
from requests.auth import HTTPBasicAuth
import json

# Configuration
SERVICENOW_URL = "https://dev273008.service-now.com"
SERVICENOW_USER = "admin"
SERVICENOW_PASS = "@nL=BMhj07Sk"
TABLE_NAME = "x_1941577_tee_se_0_ai_incident_demo"

def check_field_limits():
    print(f"[*] Checking limits for fields on {TABLE_NAME}...")
    
    # Query sys_dictionary specifically for the table and elements
    url = f"{SERVICENOW_URL}/api/now/table/sys_dictionary?sysparm_query=name={TABLE_NAME}^elementINshort_description,description,ai_case_summary&sysparm_fields=element,column_label,max_length,mandatory"
    
    try:
        response = requests.get(url, auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS))
        if response.status_code == 200:
            results = response.json().get('result', [])
            for r in results:
                print(f"Field: {r['element']} | Label: {r['column_label']} | MaxLen: {r['max_length']} | Mandatory: {r['mandatory']}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_field_limits()
