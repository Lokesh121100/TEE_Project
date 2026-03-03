import requests
from requests.auth import HTTPBasicAuth
import json

# Configuration
SERVICENOW_URL = "https://dev273008.service-now.com"
SERVICENOW_USER = "admin"
SERVICENOW_PASS = "@nL=BMhj07Sk"
TABLE_NAME = "x_1941577_tee_se_0_ai_incident_demo"

def list_all_table_fields():
    print(f"[*] Listing ALL fields for table: {TABLE_NAME}")
    url = f"{SERVICENOW_URL}/api/now/table/sys_dictionary?sysparm_query=name={TABLE_NAME}^elementISNOTEMPTY&sysparm_fields=element,column_label,max_length"
    
    try:
        response = requests.get(url, auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS))
        if response.status_code == 200:
            elements = response.json().get('result', [])
            for el in elements:
                print(f"Field: {el['element']} ({el['column_label']}) | MaxLen: {el['max_length']}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    list_all_table_fields()
