import requests
from requests.auth import HTTPBasicAuth
import json
import os

# Configuration (copied from main.py)
SERVICENOW_URL = "https://dev273008.service-now.com"
SERVICENOW_USER = "admin"
SERVICENOW_PASS = "@nL=BMhj07Sk"
TABLE_NAME = "x_1941577_tee_se_0_ai_incident_demo"

def cleanup_records():
    print(f"[*] Starting cleanup for table: {TABLE_NAME}")
    
    # 1. Fetch all records sorted by creation date (descending)
    url = f"{SERVICENOW_URL}/api/now/table/{TABLE_NAME}?sysparm_query=ORDERBYDESCsys_created_on&sysparm_fields=sys_id,short_description,number"
    
    try:
        response = requests.get(url, auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS))
        if response.status_code != 200:
            print(f"[!] Error fetching records: {response.status_code}")
            return
            
        records = response.json().get('result', [])
        total_records = len(records)
        print(f"[*] Found {total_records} total records.")
        
        if total_records <= 10:
            print("[*] 10 or fewer records found. No cleanup needed.")
            return

        # 2. Identify records to keep
        # We prioritize tickets with [AI PROCESSED] or the ones we just added
        to_keep = []
        to_delete = []
        
        # First pass: identify processed ones
        for r in records:
            if "[AI PROCESSED]" in str(r.get('short_description', '')):
                to_keep.append(r)
            if len(to_keep) >= 10:
                break
                
        # Second pass: fill up to 10 with most recent ones
        if len(to_keep) < 10:
            for r in records:
                if r not in to_keep:
                    to_keep.append(r)
                if len(to_keep) >= 10:
                    break
        
        # Identify the rest for deletion
        to_delete = [r for r in records if r not in to_keep]
        
        print(f"[*] Identified {len(to_keep)} records to keep and {len(to_delete)} to delete.")
        
        # 3. Delete records
        for i, r in enumerate(to_delete):
            sys_id = r['sys_id']
            desc = r.get('short_description', 'No description')
            del_url = f"{SERVICENOW_URL}/api/now/table/{TABLE_NAME}/{sys_id}"
            
            print(f"[{i+1}/{len(to_delete)}] Deleting record: {desc[:40]}...")
            del_resp = requests.delete(del_url, auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS))
            
            if del_resp.status_code not in [200, 204]:
                print(f"    [!] Failed to delete: {del_resp.status_code}")
                
        print("\n✅ Cleanup complete! Only 10 records remain.")
        
    except Exception as e:
        print(f"[!] Exception during cleanup: {e}")

if __name__ == "__main__":
    cleanup_records()
