from netmiko import ConnectHandler
from pprint import pprint
from dotenv import load_dotenv
import os

load_dotenv()
ROUTER_USER = os.environ.get("ROUTER_USER", "admin")
ROUTER_PASS = os.environ.get("ROUTER_PASS", "cisco")

def gigabit_status(router_ip): # <-- 1. รับ router_ip เป็นพารามิเตอร์
    """
    ตรวจสอบสถานะของ GigabitEthernet interfaces ทั้งหมดบน Router ที่ระบุแบบไดนามิก
    """
    print(f"NETMIKO: Getting Gigabit status from {router_ip}")
    
    # 2. สร้าง device_params จาก router_ip ที่ได้รับมา
    device_params = { 
        "device_type": "cisco_ios", 
        "ip": router_ip, 
        "username": ROUTER_USER, 
        "password": ROUTER_PASS, 
        "timeout": 20 
    }
    
    ans = ""
    try:
        with ConnectHandler(**device_params) as ssh:
            result_string = ssh.send_command("show ip interface brief", use_textfsm=False)
            lines = result_string.strip().split('\n')[1:]
            
            up, down, admin_down = 0, 0, 0
            detailed_statuses = []

            for line in lines:
                parts = line.split()
                if not parts or not parts[0].startswith("GigabitEthernet"):
                    continue
                
                interface_name = parts[0]
                status_parts = []
                # วนจากท้ายมาหน้าเพื่อหา status
                for part in reversed(parts):
                    if part.lower() in ['up', 'down']:
                        status_parts.insert(0, part)
                        if len(status_parts) >= 2 and status_parts[0] == 'down':
                             if parts[parts.index(part)-1] == 'administratively':
                                  status_parts.insert(0, 'administratively')
                        break
                    
                current_status = " ".join(status_parts)

                detailed_statuses.append(f"{interface_name} {current_status}")
                
                if current_status == "up up": up += 1
                elif current_status == "down down": down += 1
                elif current_status == "administratively down down": admin_down += 1
            
            details = ", ".join(detailed_statuses)
            summary = f"{up} up, {down} down, {admin_down} administratively down"
            ans = f"{details} -> {summary}"
            
            print(f"NETMIKO gigabit_status result: {ans}")
            return ans

    except Exception as e:
        print(f"An error occurred in Netmiko (gigabit_status) on {router_ip}: {e}")
        return "Error: Could not get Gigabit status."

def get_motd(router_ip):
    """
    ใช้ Netmiko เพื่ออ่านค่า MOTD จาก Router ที่ระบุ
    (เวอร์ชันนี้มี Logic การ Parse ที่ทนทานและถูกต้อง)
    """
    print(f"NETMIKO: Getting MOTD from {router_ip}")
    
    device_params = {
        "device_type": "cisco_ios", "ip": router_ip,
        "username": ROUTER_USER, "password": ROUTER_PASS,
        "timeout": 20,
    }

    try:
        with ConnectHandler(**device_params) as ssh:
            output = ssh.send_command("show banner motd", use_textfsm=False)
            
            # 1. ตรวจสอบกรณีไม่มี MOTD หรือ Output ว่างเปล่า
            if "No MOTD banner is configured" in output or not output.strip():
                return "Error: No MOTD Configured"
            else:
                # 2. แปลง Output เป็น List ของบรรทัด
                lines = output.strip().split('\n')
                
                # 3.ตรวจสอบและตัด Header ที่ไม่ต้องการออก
                # บางครั้ง output จะมีบรรทัด "The MOTD banner is:" นำหน้า
                if "The MOTD banner is:" in lines[0]:
                    # ถ้ามี Header, ให้เอาข้อความตั้งแต่บรรทัดที่สองเป็นต้นไป
                    message_lines = lines[1:]
                else:
                    # ถ้าไม่มี Header, ให้เอาทุกบรรทัด
                    message_lines = lines
                
                # 4. ประกอบร่างข้อความกลับคืนและตัดช่องว่างที่ไม่จำเป็น
                motd_message = "\n".join(message_lines).strip()
                
                return motd_message

    except Exception as e:
        print(f"NETMIKO Error getting MOTD from {router_ip}: {e}")
        return "Error: Could not connect or get MOTD"