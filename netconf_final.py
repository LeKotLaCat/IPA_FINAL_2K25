from ncclient import manager
import xmltodict
from ncclient.operations.rpc import RPCError

# เปลี่ยนเป็น IP ของ Router ที่คุณได้รับมอบหมาย
ROUTER_IP = "10.0.15.61" 

m = manager.connect(
    host=ROUTER_IP,
    port=830, # Standard NETCONF port
    username="admin",
    password="cisco",
    hostkey_verify=False
    )

def create(student_id): # <-- เพิ่ม student_id เป็นพารามิเตอร์
    # คำนวณ IP Address จาก 3 ตัวท้ายของรหัสนักศึกษา
    last_three_digits = student_id[-3:]
    x = int(last_three_digits[0])
    y = int(last_three_digits[1:])
    ip_address = f"172.{x}.{y}.1"

    # XML Payload สำหรับสร้าง Interface
    netconf_config = f"""
    <config>
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
          <name>Loopback{student_id}</name>
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
        # เช็คก่อนว่ามี interface อยู่แล้วหรือไม่
        if "No Interface" not in status(student_id):
             return f"Cannot create: Interface loopback {student_id}"
        
        netconf_reply = netconf_edit_config(netconf_config)
        xml_data = netconf_reply.xml
        print(xml_data)
        if '<ok/>' in xml_data:
            return f"Interface loopback {student_id} is created successfully"
    except RPCError as e:
        print(f"Error: {e.message}")
        return f"Error: Cannot create interface loopback {student_id}"


def delete(student_id): # <-- เพิ่ม student_id เป็นพารามิเตอร์
    # XML Payload สำหรับลบ Interface (ใช้ operation="delete")
    netconf_config = f"""
    <config>
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface operation="delete">
          <name>Loopback{student_id}</name>
        </interface>
      </interfaces>
    </config>
    """

    try:
        # เช็คก่อนว่ามี interface ให้ลบหรือไม่
        if "No Interface" in status(student_id):
             return f"Cannot delete: Interface loopback {student_id}"

        netconf_reply = netconf_edit_config(netconf_config)
        xml_data = netconf_reply.xml
        print(xml_data)
        if '<ok/>' in xml_data:
            return f"Interface loopback {student_id} is deleted successfully"
    except RPCError as e:
        print(f"Error: {e.message}")
        return f"Error: Cannot delete interface loopback {student_id}"


def enable(student_id): # <-- เพิ่ม student_id เป็นพารามิเตอร์
    # XML Payload สำหรับแก้ไขค่า 'enabled' เป็น 'true'
    netconf_config = f"""
    <config>
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
          <name>Loopback{student_id}</name>
          <enabled>true</enabled>
        </interface>
      </interfaces>
    </config>
    """

    try:
        if "No Interface" in status(student_id):
             return f"Cannot enable: Interface loopback {student_id}"
        
        netconf_reply = netconf_edit_config(netconf_config)
        xml_data = netconf_reply.xml
        print(xml_data)
        if '<ok/>' in xml_data:
            return f"Interface loopback {student_id} is enabled successfully"
    except RPCError as e:
        print(f"Error: {e.message}")
        return f"Error: Cannot enable interface loopback {student_id}"


def disable(student_id): # <-- เพิ่ม student_id เป็นพารามิเตอร์
    # XML Payload สำหรับแก้ไขค่า 'enabled' เป็น 'false'
    netconf_config = f"""
    <config>
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
          <name>Loopback{student_id}</name>
          <enabled>false</enabled>
        </interface>
      </interfaces>
    </config>
    """

    try:
        if "No Interface" in status(student_id):
             return f"Cannot shutdown: Interface loopback {student_id}"

        netconf_reply = netconf_edit_config(netconf_config)
        xml_data = netconf_reply.xml
        print(xml_data)
        if '<ok/>' in xml_data:
            return f"Interface loopback {student_id} is shutdowned successfully"
    except RPCError as e:
        print(f"Error: {e.message}")
        return f"Error: Cannot shutdown interface loopback {student_id}"

def netconf_edit_config(netconf_config):
    # ใช้ operation 'edit_config' กับ datastore 'running'
    return m.edit_config(target="running", config=netconf_config)


def status(student_id): # <-- เพิ่ม student_id เป็นพารามิเตอร์
    # XML Filter เพื่อขอข้อมูลเฉพาะ interface ที่ต้องการ
    netconf_filter = f"""
    <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
      <interface>
        <name>Loopback{student_id}</name>
      </interface>
    </interfaces-state>
    """

    try:
        # ใช้ operation 'get' เพื่อดึงข้อมูล operational state
        netconf_reply = m.get(filter=('subtree', netconf_filter))
        print(netconf_reply)
        # ใช้ 'xmltodict.parse' เพื่อแปลง XML เป็น Dictionary
        netconf_reply_dict = xmltodict.parse(netconf_reply.xml)

        # ตรวจสอบว่ามีข้อมูล interface กลับมาหรือไม่
        interface_data = netconf_reply_dict.get('data', {}).get('interfaces-state', {}).get('interface')
        if interface_data:
            # ดึงค่า admin_status และ oper_status
            admin_status = interface_data.get('admin-status')
            oper_status = interface_data.get('oper-status')
            if admin_status == 'up' and oper_status == 'up':
                return f"Interface loopback {student_id} is enabled"
            elif admin_status == 'down' and oper_status == 'down':
                return f"Interface loopback {student_id} is disabled"
        else: # no operation-state data
            return f"No Interface loopback {student_id}"
    except RPCError as e:
       print(f"Error: {e.message}")
       return f"Error: Cannot get status for interface loopback {student_id}"