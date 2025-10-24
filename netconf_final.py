from ncclient import manager
import xmltodict
from dotenv import load_dotenv
import os

load_dotenv()
ROUTER_USER = os.environ.get("ROUTER_USER", "admin")
ROUTER_PASS = os.environ.get("ROUTER_PASS", "cisco")

def connect(router_ip):
    """Helper function เพื่อสร้างการเชื่อมต่อ NETCONF"""
    try:
        return manager.connect(
            host=router_ip, port=830, username=ROUTER_USER, password=ROUTER_PASS,
            hostkey_verify=False, timeout=20
        )
    except Exception as e:
        print(f"!!! NETCONF Connection Error to {router_ip}: {e}")
        return None

def status(student_id, router_ip):
    """
    **ฟังก์ชัน status ที่ถูกแก้ไขใหม่ทั้งหมดตามแม่แบบที่ทำงานได้สำเร็จ**
    """
    interface_name = f"Loopback{student_id}"
    
    # --- FIX #1: ใช้ Filter ที่มี <filter> tag ล้อมรอบอย่างชัดเจน ---
    netconf_filter = f"""
    <filter>
      <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
          <name>{interface_name}</name>
        </interface>
      </interfaces-state>
    </filter>
    """
    
    try:
        with connect(router_ip) as m:
            if not m: return f"No Interface loopback {student_id} (checked by Netconf)"
            
            # --- FIX #2: ส่ง filter เข้าไปตรงๆ ตามแม่แบบ ---
            reply = m.get(filter=netconf_filter)
            data_dict = xmltodict.parse(reply.xml)

            # --- FIX #3: ใช้ Logic การ Parse จาก Root element ที่ปลอดภัย ---
            interface_data = data_dict.get("rpc-reply", {}).get("data", {}).get("interfaces-state", {}).get("interface")

            if interface_data:
                admin_status = interface_data.get("admin-status")
                if admin_status == "up":
                    return f"Interface loopback {student_id} is enabled (checked by Netconf)"
                else:
                    return f"Interface loopback {student_id} is disabled (checked by Netconf)"
            else:
                return f"No Interface loopback {student_id} (checked by Netconf)"
    except Exception as e:
        print(f"!!! NETCONF Status Error for {student_id} on {router_ip}: {e}")
        return f"No Interface loopback {student_id} (checked by Netconf)"

# --- ฟังก์ชันที่เหลือ (create, delete, enable, disable) ไม่ต้องแก้ไข ---
# --- เพราะมันทำงานได้ดีอยู่แล้ว หรือจะทำงานได้ดีขึ้นเมื่อ status() ถูกซ่อมแล้ว ---

def create(student_id, router_ip):
    if "No Interface" not in status(student_id, router_ip):
        return f"Cannot create: Interface loopback {student_id}"

    last_three = student_id[-3:]
    ip_address = f"172.{last_three[0]}.{last_three[1:]}.1"
    interface_name = f"Loopback{student_id}"

    netconf_config = f"""
    <config>
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
          <name>{interface_name}</name>
          <description>Created by NETCONF for {student_id}</description>
          <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:softwareLoopback</type>
          <enabled>true</enabled>
          <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip">
            <address>
              <ip>{ip_address}</ip>
              <netmask>255.255.255.0</netmask>
            </address>
          </ipv4>
        </interface>
      </interfaces>
    </config>
    """
    try:
        with connect(router_ip) as m:
            if not m: return f"Cannot create: Interface loopback {student_id}"
            reply = m.edit_config(target="running", config=netconf_config)
            
            if "<ok/>" in reply.xml:
                return f"Interface loopback {student_id} is created successfully using Netconf"
            else:
                print(f"NETCONF Create Non-OK Reply: {reply.xml}")
                return f"Cannot create: Interface loopback {student_id}"
    except Exception as e:
        print(f"!!! NETCONF Create Exception for {student_id} on {router_ip}: {e}")
        return f"Cannot create: Interface loopback {student_id}"

def delete(student_id, router_ip):
    if "No Interface" not in status(student_id, router_ip):
        return f"Cannot delete: Interface loopback {student_id}"
        
    interface_name = f"Loopback{student_id}"
    netconf_config = f"""<config><interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"><interface operation="delete"><name>{interface_name}</name></interface></interfaces></config>"""
    try:
        with connect(router_ip) as m:
            if not m: return f"Cannot delete: Interface loopback {student_id}"
            reply = m.edit_config(target="running", config=netconf_config)
            if "<ok/>" in reply.xml:
                return f"Interface loopback {student_id} is deleted successfully using Netconf"
    except Exception as e:
        print(f"!!! NETCONF Delete Exception: {e}")
    return f"Cannot delete: Interface loopback {student_id}"

def enable(student_id, router_ip):
    current_state = status(student_id, router_ip)
    if "No Interface" in current_state or "is enabled" in current_state:
        return f"Cannot enable: Interface loopback {student_id}"

    interface_name = f"Loopback{student_id}"
    netconf_config = f"""<config><interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"><interface><name>{interface_name}</name><enabled>true</enabled></interface></interfaces></config>"""
    try:
        with connect(router_ip) as m:
            if not m: return f"Cannot enable: Interface loopback {student_id}"
            reply = m.edit_config(target="running", config=netconf_config)
            if "<ok/>" in reply.xml:
                return f"Interface loopback {student_id} is enabled successfully using Netconf"
    except Exception as e:
        print(f"!!! NETCONF Enable Exception: {e}")
    return f"Cannot enable: Interface loopback {student_id}"

def disable(student_id, router_ip):
    current_state = status(student_id, router_ip)
    if "No Interface" in current_state or "is disabled" in current_state:
        return f"Cannot shutdown: Interface loopback {student_id}"

    interface_name = f"Loopback{student_id}"
    netconf_config = f"""<config><interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"><interface><name>{interface_name}</name><enabled>false</enabled></interface></interfaces></config>"""
    try:
        with connect(router_ip) as m:
            if not m: return f"Cannot shutdown: Interface loopback {student_id}"
            reply = m.edit_config(target="running", config=netconf_config)
            if "<ok/>" in reply.xml:
                return f"Interface loopback {student_id} is shutdowned successfully using Netconf"
            else:
                return f"Cannot shutdown: Interface loopback {student_id} (checked by Netconf)"
    except Exception as e:
        print(f"!!! NETCONF Disable Exception: {e}")
        return f"Cannot shutdown: Interface loopback {student_id} (checked by Netconf)"