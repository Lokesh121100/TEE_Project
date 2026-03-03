import requests
from requests.auth import HTTPBasicAuth
import json

# Configuration
SERVICENOW_URL = "https://dev273008.service-now.com"
SERVICENOW_USER = "admin"
SERVICENOW_PASS = "@nL=BMhj07Sk"
TABLE_NAME = "x_1941577_tee_se_0_ai_incident_demo"

def list_all_fields():
    print(f"[*] Listing ALL fields for table: {TABLE_NAME}")
    
    # Query sys_dictionary for the table
    url = f"{SERVICENOW_URL}/api/now/table/sys_dictionary?sysparm_query=name={TABLE_NAME}^ORname=task^elementISNOTEMPTY&sysparm_fields=element,column_label,max_length"
    
    try:
        response = requests.get(url, auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS))
        if response.status_code == 200:
            elements = response.json().get('result', [])
            found = False
            for el in elements:
                if 'description' in el['element'].lower():
                    print(f"Found: {el['element']} ({el['column_label']}) | MaxLen: {el['max_length']}")
                    found = True
            if not found:
                print("[!] No 'description' field found in the dictionary for this table or its parent.")
                # List top 20 fields just to see what we HAVE
                print("\nTop 20 Fields available:")
                for el in elements[:20]:
                    print(f"- {el['element']} ({el['column_label']})")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    list_all_fields()
