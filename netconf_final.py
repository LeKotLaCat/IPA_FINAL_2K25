#######################################################################################
# Name: PETCHPRAETHONG INUTHAI
# student ID: 66070139
# GitHub Repo: https://github.com/LeKotLaCat/IPA_FINAL_2K25.git
#######################################################################################

from ncclient import manager
import xmltodict
from ncclient.operations.rpc import RPCError

def _execute_netconf(router_ip, config_data=None, filter_data=None):
    """Helper function กลาง สำหรับเชื่อมต่อ, ส่งคำสั่ง, และปิด session"""
    m = None
    try:
        m = manager.connect(host=router_ip, port=830, username="admin", password="cisco", hostkey_verify=False, timeout=20)
        if config_data:
            return m.edit_config(target="running", config=config_data)
        if filter_data:
            return m.get(filter=('subtree', filter_data))
    finally:
        if m:
            m.close_session()

def create(student_id, router_ip):
    if "No Interface" not in status(student_id, router_ip):
        return f"Cannot create: Interface loopback {student_id}"

    last_three = student_id[-3:]
    ip_address = f"172.{last_three[0]}.{last_three[1:]}.1"

    netconf_config = f"""<config><interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"><interface><name>Loopback{student_id}</name><type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:softwareLoopback</type><enabled>true</enabled><ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip"><address><ip>{ip_address}</ip><netmask>255.255.255.0</netmask></address></ipv4></interface></interfaces></config>"""
    try:
        reply = _execute_netconf(router_ip, config_data=netconf_config)
        if '<ok/>' in reply.xml:
            return f"Interface loopback {student_id} is created successfully using Netconf"
    except RPCError as e:
        print(f"RPCError: {e}")
    return f"Error: Cannot create interface loopback {student_id}"

def delete(student_id, router_ip):
    if "No Interface" in status(student_id, router_ip):
        return f"Cannot delete: Interface loopback {student_id}"

    netconf_config = f"""<config><interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"><interface operation="delete"><name>Loopback{student_id}</name></interface></interfaces></config>"""
    try:
        reply = _execute_netconf(router_ip, config_data=netconf_config)
        if '<ok/>' in reply.xml:
            return f"Interface loopback {student_id} is deleted successfully using Netconf"
    except RPCError as e:
        print(f"RPCError: {e}")
    return f"Error: Cannot delete interface loopback {student_id}"

def enable(student_id, router_ip):
    if "No Interface" in status(student_id, router_ip):
        return f"Cannot enable: Interface loopback {student_id}"
        
    netconf_config = f"""<config><interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"><interface><name>Loopback{student_id}</name><enabled>true</enabled></interface></interfaces></config>"""
    try:
        reply = _execute_netconf(router_ip, config_data=netconf_config)
        if '<ok/>' in reply.xml:
            return f"Interface loopback {student_id} is enabled successfully using Netconf"
    except RPCError as e:
        print(f"RPCError: {e}")
    return f"Error: Cannot enable interface loopback {student_id}"

def disable(student_id, router_ip):
    if "No Interface" in status(student_id, router_ip):
        return f"Cannot shutdown: Interface loopback {student_id}"

    netconf_config = f"""<config><interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"><interface><name>Loopback{student_id}</name><enabled>false</enabled></interface></interfaces></config>"""
    try:
        reply = _execute_netconf(router_ip, config_data=netconf_config)
        if '<ok/>' in reply.xml:
            return f"Interface loopback {student_id} is shutdowned successfully using Netconf"
    except RPCError as e:
        print(f"RPCError: {e}")
    return f"Error: Cannot shutdown interface loopback {student_id}"

def status(student_id, router_ip):
    netconf_filter = f"""<interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"><interface><name>Loopback{student_id}</name></interface></interfaces-state>"""
    try:
        reply = _execute_netconf(router_ip, filter_data=netconf_filter)
        reply_dict = xmltodict.parse(reply.xml)
        interface_data = reply_dict.get('data', {}).get('interfaces-state', {}).get('interface')
        if interface_data:
            if interface_data.get('admin-status') == 'up' and interface_data.get('oper-status') == 'up':
                return f"Interface loopback {student_id} is enabled (checked by Netconf)"
            else:
                return f"Interface loopback {student_id} is disabled (checked by Netconf)"
        else:
            return f"No Interface loopback {student_id} (checked by Netconf)"
    except Exception as e:
        print(f"Error checking status: {e}")
        return f"No Interface loopback {student_id} (checked by Netconf)"


