#######################################################################################
# Name: PETCHPRAETHONG INUTHAI
# student ID: 66070139
# GitHub Repo: https://github.com/LeKotLaCat/IPA_FINAL_2K25.git
#######################################################################################

import json
import requests
import time
from dotenv import load_dotenv
import os

load_dotenv()
ROUTER_USER = os.environ.get("ROUTER_USER")
ROUTER_PASS = os.environ.get("ROUTER_PASS")

basicauth = (ROUTER_USER, ROUTER_PASS) 

# ปิดคำเตือน SSL InsecureRequestWarning
requests.packages.urllib3.disable_warnings()

# --- Global Configurations ---
headers = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}


# --- Helper Function ---
def _get_status(student_id, router_ip):
    """Helper function ภายใน ไว้เช็คสถานะ Operational State"""
    api_url = f"https://{router_ip}/restconf/data/ietf-interfaces:interfaces-state/interface=Loopback{student_id}"
    try:
        resp = requests.get(api_url, auth=basicauth, headers=headers, verify=False, timeout=10)
        if resp.status_code == 404:
            return "not_found", None
        elif resp.status_code == 200:
            return "found", resp.json()
        else:
            print(f"RESTCONF STATUS CHECK ERROR on {router_ip}: {resp.status_code}")
            return "error", None
    except requests.exceptions.RequestException as e:
        print(f"RESTCONF CONNECTION ERROR on {router_ip}: {e}")
        return "error", None

# --- Main Functions ---
def create(student_id, router_ip):
    current_status, _ = _get_status(student_id, router_ip)
    if current_status == "found":
        return f"Cannot create: Interface loopback {student_id}"

    api_url = f"https://{router_ip}/restconf/data/ietf-interfaces:interfaces/interface=Loopback{student_id}"
    last_three = student_id[-3:]
    ip_address = f"172.{last_three[0]}.{last_three[1:]}.1"
    
    yangConfig = { "ietf-interfaces:interface": { "name": f"Loopback{student_id}", "type": "iana-if-type:softwareLoopback", "enabled": True, "ietf-ip:ipv4": { "address": [{ "ip": ip_address, "netmask": "255.255.255.0" }] } } }
    try:
        resp = requests.put(api_url, data=json.dumps(yangConfig), auth=basicauth, headers=headers, verify=False, timeout=10)
        if resp.status_code in [201, 204]:
            return f"Interface loopback {student_id} is created successfully using Restconf"
        else:
            print(f"RESTCONF CREATE FAILED on {router_ip}: {resp.status_code} - {resp.text}")
            return f"Cannot create: Interface loopback {student_id}"
    except requests.exceptions.RequestException as e:
        print(f"RESTCONF CONNECTION ERROR on {router_ip}: {e}")
        return f"Cannot create: Interface loopback {student_id}"

def delete(student_id, router_ip):
    api_url = f"https://{router_ip}/restconf/data/ietf-interfaces:interfaces/interface=Loopback{student_id}"
    try:
        resp = requests.delete(api_url, auth=basicauth, headers=headers, verify=False, timeout=10)
        if resp.status_code == 204:
            return f"Interface loopback {student_id} is deleted successfully using Restconf"
        elif resp.status_code == 404:
            print(f"INFO: Attempted to delete a non-existent interface on {router_ip} (received 404).")
            return f"Cannot delete: Interface loopback {student_id}"
        else:
            print(f"RESTCONF DELETE FAILED on {router_ip}: Unexpected status {resp.status_code} - {resp.text}")
            return f"Cannot delete: Interface loopback {student_id}"
    except requests.exceptions.RequestException as e:
        print(f"RESTCONF CONNECTION ERROR on {router_ip}: {e}")
        return f"Cannot delete: Interface loopback {student_id}"

def enable(student_id, router_ip):
    current_status, data = _get_status(student_id, router_ip)
    if current_status == "not_found" or (current_status == "found" and data["ietf-interfaces:interface"]["admin-status"] == "up"):
        return f"Cannot enable: Interface loopback {student_id}"
    
    api_url = f"https://{router_ip}/restconf/data/ietf-interfaces:interfaces/interface=Loopback{student_id}/enabled"
    yangConfig = { "ietf-interfaces:enabled": True }
    try:
        resp = requests.put(api_url, data=json.dumps(yangConfig), auth=basicauth, headers=headers, verify=False, timeout=10)
        if resp.status_code == 204:
            return f"Interface loopback {student_id} is enabled successfully using Restconf"
        else:
            print(f"RESTCONF ENABLE FAILED on {router_ip}: {resp.status_code} - {resp.text}")
            return f"Cannot enable: Interface loopback {student_id}"
    except requests.exceptions.RequestException as e:
        print(f"RESTCONF CONNECTION ERROR on {router_ip}: {e}")
        return f"Cannot enable: Interface loopback {student_id}"

def disable(student_id, router_ip):
    current_status, data = _get_status(student_id, router_ip)
    if current_status == "not_found" or (current_status == "found" and data["ietf-interfaces:interface"]["admin-status"] == "down"):
        return f"Cannot shutdown: Interface loopback {student_id}"
        
    api_url = f"https://{router_ip}/restconf/data/ietf-interfaces:interfaces/interface=Loopback{student_id}/enabled"
    yangConfig = { "ietf-interfaces:enabled": False }
    try:
        resp = requests.put(api_url, data=json.dumps(yangConfig), auth=basicauth, headers=headers, verify=False, timeout=10)
        if resp.status_code == 204:
            return f"Interface loopback {student_id} is shutdowned successfully using Restconf"
        else:
            print(f"RESTCONF DISABLE FAILED on {router_ip}: {resp.status_code} - {resp.text}")
            return f"Cannot shutdown: Interface loopback {student_id}"
    except requests.exceptions.RequestException as e:
        print(f"RESTCONF CONNECTION ERROR on {router_ip}: {e}")
        return f"Cannot shutdown: Interface loopback {student_id}"

def status(student_id, router_ip):
    current_status, data = _get_status(student_id, router_ip)
    if current_status == "not_found":
        return f"No Interface loopback {student_id} (checked by Restconf)"
    elif current_status == "found":
        interface_state = data["ietf-interfaces:interface"]
        if interface_state["admin-status"] == 'up':
            return f"Interface loopback {student_id} is enabled (checked by Restconf)"
        else:
            return f"Interface loopback {student_id} is disabled (checked by Restconf)"
    else: # Fallback for connection errors
        return f"No Interface loopback {student_id} (checked by Restconf)"

# --- END OF FILE ---