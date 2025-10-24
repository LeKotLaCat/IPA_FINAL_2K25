from netmiko import ConnectHandler
from pprint import pprint
from dotenv import load_dotenv
import os

load_dotenv()
ROUTER_USER = os.environ.get("ROUTER_USER", "admin")
ROUTER_PASS = os.environ.get("ROUTER_PASS", "cisco")

def gigabit_status():
    """
    ตรวจสอบสถานะของ GigabitEthernet interfaces ทั้งหมดบน Router ที่กำหนด
    ฟังก์ชันนี้จะทำงานกับ IP ที่ระบุไว้ภายใน (hardcoded) ตามโจทย์เดิม
    """
    # ระบุ IP ของ Router ที่จะตรวจสอบ (ตามโจทย์เดิมของ Part 2)
    device_ip = "10.0.15.61" # หรือ IP หลักของ pod ที่คุณใช้สำหรับ gigabit_status
    
    device_params = { 
        "device_type": "cisco_ios", 
        "ip": device_ip, 
        "username": ROUTER_USER, 
        "password": ROUTER_PASS, 
        "timeout": 20 
    }
    
    ans = ""
    try:
        with ConnectHandler(**device_params) as ssh:
            # ดึงข้อมูลสถานะ interface เป็น string ธรรมดา
            result_string = ssh.send_command("show ip interface brief", use_textfsm=False)
            
            # แยกผลลัพธ์ออกเป็นทีละบรรทัด และข้ามบรรทัดหัวข้อ (บรรทัดแรก)
            lines = result_string.strip().split('\n')[1:]
            
            up, down, admin_down = 0, 0, 0
            detailed_statuses = []

            # วนลูปตรวจสอบทีละบรรทัด
            for line in lines:
                parts = line.split()
                # ข้ามบรรทัดว่าง หรือบรรทัดที่ไม่ใช่ GigabitEthernet
                if not parts or not parts[0].startswith("GigabitEthernet"):
                    continue
                
                interface_name = parts[0]
                # สถานะจะอยู่ที่ 2-3 ตำแหน่งสุดท้ายของ list
                # เราจะรวมมันเข้าด้วยกันเพื่อให้ได้ status ที่สมบูรณ์
                current_status = " ".join(parts[4:])

                # เพิ่มสถานะของ interface นี้เข้าไปใน list
                detailed_statuses.append(f"{interface_name} {current_status}")
                
                # นับจำนวนตามสถานะ
                if current_status == "up":
                    up += 1
                elif current_status == "down":
                    down += 1
                elif current_status == "administratively down":
                    admin_down += 1
            
            # ประกอบร่างข้อความผลลัพธ์สุดท้ายตาม Format ที่โจทย์ต้องการ
            details = ", ".join(detailed_statuses)
            summary = f"{up} up, {down} down, {admin_down} administratively down"
            ans = f"{details} -> {summary}"
            
            print(f"NETMIKO gigabit_status result: {ans}")
            return ans

    except Exception as e:
        print(f"An error occurred in Netmiko (gigabit_status) on {device_ip}: {e}")
        return "Error: Could not get Gigabit status."

# --- START: ฟังก์ชันที่แก้ไขแล้ว ---

def get_motd(router_ip):
    """
    ใช้ Netmiko เพื่ออ่านค่า MOTD จาก Router ที่ระบุ
    (เวอร์ชันนี้มี Logic การ Parse ที่ทนทานและถูกต้อง)
    """
    print(f"NETMIKO: Getting MOTD from {router_ip}")
    
    device_params = {
        "device_type": "cisco_ios", "ip": router_ip,
        "username": ROUTER_USER, "password": ROUTER_PASS,
        "timeout": 20, # แก้จาก conn_timeout เป็น timeout
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
                
                # 3. (Logic ใหม่) ตรวจสอบและตัด Header ที่ไม่ต้องการออก
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