#######################################################################################
# Name: PETCHPRAETHONG INUTHAI
# student ID: 66070139
# GitHub Repo: https://github.com/LeKotLaCat/IPA_FINAL_2K25.git
#######################################################################################

import json
import requests
requests.packages.urllib3.disable_warnings()

headers = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}
basicauth = ("admin", "cisco")

def _get_status(student_id, router_ip):
    """Helper function ภายใน ไว้เช็คสถานะ, จะได้ไม่พิมพ์โค้ดซ้ำ"""
    api_url = f"https://{router_ip}/restconf/data/ietf-interfaces:interfaces-state/interface=Loopback{student_id}"
    resp = requests.get(api_url, auth=basicauth, headers=headers, verify=False)
    if resp.status_code == 404:
        return "not_found", None
    elif resp.status_code == 200:
        return "found", resp.json()
    else:
        return "error", None

def create(student_id, router_ip):
    # ตรวจสอบก่อนว่ามี interface อยู่แล้วหรือไม่
    current_status, _ = _get_status(student_id, router_ip)
    if current_status == "found":
        return f"Cannot create: Interface loopback {student_id}"

    api_url = f"https://{router_ip}/restconf/data/ietf-interfaces:interfaces/interface=Loopback{student_id}"
    
    last_three = student_id[-3:]
    ip_address = f"172.{last_three[0]}.{last_three[1:]}.1"
    
    yangConfig = { "ietf-interfaces:interface": { "name": f"Loopback{student_id}", "type": "iana-if-type:softwareLoopback", "enabled": True, "ietf-ip:ipv4": { "address": [{ "ip": ip_address, "netmask": "255.255.255.0" }] } } }

    resp = requests.put(api_url, data=json.dumps(yangConfig), auth=basicauth, headers=headers, verify=False)

    if resp.status_code in [201, 204]:
        return f"Interface loopback {student_id} is created successfully using Restconf"
    else:
        return f"Error: Cannot create interface loopback {student_id} (Code: {resp.status_code})"

def delete(student_id, router_ip):
    current_status, _ = _get_status(student_id, router_ip)
    if current_status == "not_found":
        return f"Cannot delete: Interface loopback {student_id}"

    api_url = f"https://{router_ip}/restconf/data/ietf-interfaces:interfaces/interface=Loopback{student_id}"
    resp = requests.delete(api_url, auth=basicauth, headers=headers, verify=False)

    if resp.status_code == 204:
        return f"Interface loopback {student_id} is deleted successfully using Restconf"
    else:
        return f"Error: Cannot delete interface loopback {student_id} (Code: {resp.status_code})"

def enable(student_id, router_ip):
    current_status, _ = _get_status(student_id, router_ip)
    if current_status == "not_found":
        return f"Cannot enable: Interface loopback {student_id}"
    
    api_url = f"https://{router_ip}/restconf/data/ietf-interfaces:interfaces/interface=Loopback{student_id}/enabled"
    yangConfig = { "ietf-interfaces:enabled": True }

    resp = requests.put(api_url, data=json.dumps(yangConfig), auth=basicauth, headers=headers, verify=False)
    if resp.status_code == 204:
        return f"Interface loopback {student_id} is enabled successfully using Restconf"
    else:
        return f"Error: Cannot enable interface loopback {student_id} (Code: {resp.status_code})"

def disable(student_id, router_ip):
    current_status, _ = _get_status(student_id, router_ip)
    if current_status == "not_found":
        return f"Cannot shutdown: Interface loopback {student_id}"
        
    api_url = f"https://{router_ip}/restconf/data/ietf-interfaces:interfaces/interface=Loopback{student_id}/enabled"
    yangConfig = { "ietf-interfaces:enabled": False }

    resp = requests.put(api_url, data=json.dumps(yangConfig), auth=basicauth, headers=headers, verify=False)
    if resp.status_code == 204:
        return f"Interface loopback {student_id} is shutdowned successfully using Restconf"
    else:
        return f"Error: Cannot shutdown interface loopback {student_id} (Code: {resp.status_code})"

def status(student_id, router_ip):
    current_status, data = _get_status(student_id, router_ip)
    
    if current_status == "not_found":
        return f"No Interface loopback {student_id} (checked by Restconf)"
    elif current_status == "found":
        interface_state = data["ietf-interfaces:interface"]
        if interface_state["admin-status"] == 'up' and interface_state["oper-status"] == 'up':
            return f"Interface loopback {student_id} is enabled (checked by Restconf)"
        else:
            return f"Interface loopback {student_id} is disabled (checked by Restconf)"
    else:
        return f"Error: Cannot get status for interface loopback {student_id} (checked by Restconf)"