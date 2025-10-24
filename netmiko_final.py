from netmiko import ConnectHandler
from pprint import pprint

# เปลี่ยนเป็น IP ของ Router ที่คุณได้รับมอบหมาย
device_ip = "10.0.15.61"
username = "admin"
password = "cisco"

device_params = {
    "device_type": "cisco_ios",
    "ip": device_ip,
    "username": username,
    "password": password,
    "conn_timeout": 30,
}

def gigabit_status():
    ans = ""
    try:
        with ConnectHandler(**device_params) as ssh:
            up = 0
            down = 0
            admin_down = 0
            detailed_statuses = []

            # ดึงข้อมูลเป็น string ธรรมดา โดยไม่ใช้ TextFSM
            result_string = ssh.send_command("show ip interface brief", use_textfsm=False)
            
            # แยกผลลัพธ์ออกเป็นทีละบรรทัด และข้ามบรรทัดหัวข้อ (บรรทัดแรก)
            lines = result_string.strip().split('\n')[1:]

            for line in lines:
                parts = line.split() # แยกแต่ละบรรทัดด้วยช่องว่าง
                if not parts: # ข้ามบรรทัดที่ว่างเปล่า
                    continue

                interface_name = parts[0]
                
                # กรองเอาเฉพาะ Interface ที่เราสนใจ
                if interface_name.startswith("GigabitEthernet"):
                    # สถานะจะอยู่ที่ 2 ตำแหน่งสุดท้ายของ list (เช่น 'administratively', 'down')
                    # หรือตำแหน่งเดียวก่อนสุดท้าย (เช่น 'up', 'down')
                    # เราจะตรวจสอบจาก Protocol status (ตัวสุดท้าย) ก่อน
                    protocol_status = parts[-1]
                    admin_status = parts[-2]

                    current_status = ""
                    if admin_status == "administratively" and protocol_status == "down":
                        current_status = "administratively down"
                    elif protocol_status == "up":
                        current_status = "up"
                    elif protocol_status == "down":
                        current_status = "down"
                    else:
                        continue # ถ้าไม่เจอสถานะที่รู้จักก็ข้ามไป

                    # สร้างข้อความสำหรับแต่ละ interface
                    status_line = f"{interface_name} {current_status}"
                    detailed_statuses.append(status_line)
                    
                    # นับจำนวนตามสถานะ
                    if current_status == "up":
                        up += 1
                    elif current_status == "down":
                        down += 1
                    elif current_status == "administratively down":
                        admin_down += 1
            
            # ประกอบร่างข้อความสุดท้าย
            details = ", ".join(detailed_statuses)
            summary = f"{up} up, {down} down, {admin_down} administratively down"
            ans = f"{details} -> {summary}"
            
            pprint(ans)
            return ans
    
    except Exception as e:
        print(f"An error occurred in Netmiko: {e}")
        return "Error: Could not connect to the device or process the command."