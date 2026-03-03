import requests
from requests.auth import HTTPBasicAuth
import json

# Configuration
SERVICENOW_URL = "https://dev273008.service-now.com"
SERVICENOW_USER = "admin"
SERVICENOW_PASS = "@nL=BMhj07Sk"
TABLE_NAME = "x_1941577_tee_se_0_ai_incident_demo"

def check_table_dictionary():
    print(f"[*] Checking dictionary for table: {TABLE_NAME}")
    
    # Query sys_dictionary for the table
    url = f"{SERVICENOW_URL}/api/now/table/sys_dictionary?sysparm_query=name={TABLE_NAME}^ORname=task&sysparm_fields=element,column_label,max_length,mandatory,read_only"
    
    try:
        response = requests.get(url, auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS))
        if response.status_code != 200:
            print(f"[!] Error fetching dictionary: {response.status_code}")
            return
            
        elements = response.json().get('result', [])
        print(f"[*] Found {len(elements)} dictionary entries.")
        
        for el in elements:
            # Check for critical fields
            field_name = el.get('element', '')
            label = el.get('column_label', '')
            if field_name in ['short_description', 'description', 'ai_case_summary', 'ai_automation_notes', 'ai_suggested_resolution', 'number']:
                print(f"Field: {field_name} ({label})")
                print(f"  Max Length: {el.get('max_length')}")
                print(f"  Mandatory: {el.get('mandatory')}")
                print(f"  Read Only: {el.get('read_only')}")
                print("-" * 30)
                
    except Exception as e:
        print(f"[!] Exception: {e}")

if __name__ == "__main__":
    check_table_dictionary()
