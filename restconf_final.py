import json
import requests
requests.packages.urllib3.disable_warnings()

# Router IP Address is 10.0.15.61 (สมมติ IP นี้, ให้เปลี่ยนเป็น IP ของคุณ)
ROUTER_IP = "10.0.15.61"
# URL พื้นฐานสำหรับ RESTCONF configuration data
api_url_base = f"https://{ROUTER_IP}/restconf/data/ietf-interfaces:interfaces/interface="

# the RESTCONF HTTP headers, including the Accept and Content-Type
# Two YANG data formats (JSON and XML) work with RESTCONF 
headers = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}
basicauth = ("admin", "cisco")


def create(student_id): # <-- เพิ่ม student_id เป็นพารามิเตอร์
    # คำนวณ IP Address จาก 3 ตัวท้ายของรหัสนักศึกษา
    last_three_digits = student_id[-3:]
    x = int(last_three_digits[0])
    y = int(last_three_digits[1:])
    ip_address = f"172.{x}.{y}.1"

    yangConfig = {
        "ietf-interfaces:interface": {
            "name": f"Loopback{student_id}",
            "type": "iana-if-type:softwareLoopback",
            "enabled": True,
            "ietf-ip:ipv4": {
                "address": [
                    {
                        "ip": ip_address,
                        "netmask": "255.255.255.0"
                    }
                ]
            }
        }
    }

    resp = requests.put(
        url=f"{api_url_base}Loopback{student_id}", 
        data=json.dumps(yangConfig), 
        auth=basicauth, 
        headers=headers, 
        verify=False
        )

    if(resp.status_code >= 200 and resp.status_code <= 299):
        print("STATUS OK: {}".format(resp.status_code))
        return f"Interface loopback {student_id} is created successfully"
    else:
        print('Error. Status Code: {}'.format(resp.status_code))
        # เพิ่มเงื่อนไขเช็คว่ามีอยู่แล้วหรือไม่
        if resp.status_code == 409: # Conflict
             return f"Cannot create: Interface loopback {student_id}"
        return f"Error: Cannot create interface loopback {student_id}"


def delete(student_id): # <-- เพิ่ม student_id เป็นพารามิเตอร์
    resp = requests.delete(
        url=f"{api_url_base}Loopback{student_id}", 
        auth=basicauth, 
        headers=headers, 
        verify=False
        )

    if(resp.status_code >= 200 and resp.status_code <= 299):
        print("STATUS OK: {}".format(resp.status_code))
        return f"Interface loopback {student_id} is deleted successfully"
    else:
        print('Error. Status Code: {}'.format(resp.status_code))
        # เพิ่มเงื่อนไขเช็คว่าไม่มี interface ให้ลบ
        if resp.status_code == 404: # Not Found
            return f"Cannot delete: Interface loopback {student_id}"
        return f"Error: Cannot delete interface loopback {student_id}"


def enable(student_id): # <-- เพิ่ม student_id เป็นพารามิเตอร์
    yangConfig = {
        "ietf-interfaces:interface": {
            "name": f"Loopback{student_id}",
            "enabled": True
        }
    }

    resp = requests.patch( # ใช้ PATCH สำหรับการแก้ไขบางส่วน
        url=f"{api_url_base}Loopback{student_id}", 
        data=json.dumps(yangConfig), 
        auth=basicauth, 
        headers=headers, 
        verify=False
        )

    if(resp.status_code >= 200 and resp.status_code <= 299):
        print("STATUS OK: {}".format(resp.status_code))
        return f"Interface loopback {student_id} is enabled successfully"
    else:
        print('Error. Status Code: {}'.format(resp.status_code))
        if resp.status_code == 404:
            return f"Cannot enable: Interface loopback {student_id}"
        return f"Error: Cannot enable interface loopback {student_id}"


def disable(student_id): # <-- เพิ่ม student_id เป็นพารามิเตอร์
    yangConfig = {
        "ietf-interfaces:interface": {
            "name": f"Loopback{student_id}",
            "enabled": False
        }
    }

    resp = requests.patch( # ใช้ PATCH สำหรับการแก้ไขบางส่วน
        url=f"{api_url_base}Loopback{student_id}", 
        data=json.dumps(yangConfig), 
        auth=basicauth, 
        headers=headers, 
        verify=False
        )

    if(resp.status_code >= 200 and resp.status_code <= 299):
        print("STATUS OK: {}".format(resp.status_code))
        return f"Interface loopback {student_id} is shutdowned successfully"
    else:
        print('Error. Status Code: {}'.format(resp.status_code))
        if resp.status_code == 404:
            return f"Cannot shutdown: Interface loopback {student_id}"
        return f"Error: Cannot shutdown interface loopback {student_id}"


def status(student_id): # <-- เพิ่ม student_id เป็นพารามิเตอร์
    api_url_status = f"https://{ROUTER_IP}/restconf/data/ietf-interfaces:interfaces-state/interface=Loopback{student_id}"

    resp = requests.get(
        url=api_url_status, 
        auth=basicauth, 
        headers=headers, 
        verify=False
        )

    if(resp.status_code >= 200 and resp.status_code <= 299):
        print("STATUS OK: {}".format(resp.status_code))
        response_json = resp.json()
        admin_status = response_json["ietf-interfaces:interface"]["admin-status"]
        oper_status = response_json["ietf-interfaces:interface"]["oper-status"]
        if admin_status == 'up' and oper_status == 'up':
            return f"Interface loopback {student_id} is enabled"
        elif admin_status == 'down' and oper_status == 'down':
            return f"Interface loopback {student_id} is disabled"
    elif(resp.status_code == 404):
        print("STATUS NOT FOUND: {}".format(resp.status_code))
        return f"No Interface loopback {student_id}"
    else:
        print('Error. Status Code: {}'.format(resp.status_code))
        return f"Error: Cannot get status for interface loopback {student_id}"