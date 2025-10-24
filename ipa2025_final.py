#######################################################################################
# Name: PETCHPRAETHONG INUTHAI
# student ID: 66070139
# GitHub Repo: https://github.com/LeKotLaCat/IPA_FINAL_2K25.git
#######################################################################################
#######################################################################################
# Yourname:
# Your student ID:
# Your GitHub Repo: 
#######################################################################################
import os
import requests
import json
import time
from dotenv import load_dotenv
from requests_toolbelt.multipart.encoder import MultipartEncoder

# โหลดค่าจากไฟล์ .env
load_dotenv()

# Import modules สำหรับจัดการ Router
import restconf_final 
import netconf_final 
import netmiko_final
import ansible_final

# อ่านค่า Config จาก Environment Variables
ACCESS_TOKEN = os.environ.get("WEBEX_ACCESS_TOKEN")
ROOM_ID = os.environ.get("WEBEX_ROOM_ID")
MY_STUDENT_ID = os.environ.get("MY_STUDENT_ID")

# ตรวจสอบว่าตั้งค่า Environment Variables ครบถ้วนหรือไม่
if not all([ACCESS_TOKEN, ROOM_ID, MY_STUDENT_ID]):
    raise Exception("\n!!! กรุณาสร้างไฟล์ .env และใส่ค่าให้ครบถ้วน !!!")

# --- START: 2025 Logic ---
user_sessions = {} 
VALID_IPS = ["10.0.15.61", "10.0.15.62", "10.0.15.63", "10.0.15.64", "10.0.15.65"]
PART1_COMMANDS = ["create", "delete", "enable", "disable", "status"]
PART2_COMMANDS = ["gigabit_status", "showrun"]
# --- END: 2025 Logic ---

while True:
    time.sleep(1)

    getParameters = {"roomId": ROOM_ID, "max": 1}
    getHTTPHeader = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    try:
        r = requests.get("https://webexapis.com/v1/messages", params=getParameters, headers=getHTTPHeader)
        r.raise_for_status() # เช็ค HTTP Error
        json_data = r.json()
        if not json_data["items"]: continue
    except requests.exceptions.RequestException as e:
        print(f"Error fetching messages: {e}")
        continue

    message = json_data["items"][0]["text"]
    print("Received message: " + message)

    # --- START: 2025 New Command Parsing Logic (Refined) ---
    if message.startswith(f"/{MY_STUDENT_ID}"):
        parts = message.split()
        num_parts = len(parts)
        responseMessage = ""
        filename = None
        
        # ตรวจสอบว่าผู้ใช้เคยเลือก method แล้วหรือยัง
        method_is_set = MY_STUDENT_ID in user_sessions

        # กรณีที่ 1: คำสั่งมี 2 ส่วน (e.g., /... restconf or /... create)
        if num_parts == 2:
            command = parts[1]
            
            if command in ["restconf", "netconf"]:
                user_sessions[MY_STUDENT_ID] = {"method": command}
                responseMessage = f"Ok: {command.capitalize()}"
            
            elif command in PART2_COMMANDS:
                if command == "gigabit_status":
                    responseMessage = netmiko_final.gigabit_status()
                elif command == "showrun":
                    router_name = 'CSR1KV-Pod1-1'
                    responseMessage, filename = ansible_final.showrun(MY_STUDENT_ID, router_name)
            
            elif command in PART1_COMMANDS:
                if not method_is_set:
                    responseMessage = "Error: No method specified"
                else:
                    responseMessage = "Error: No IP specified"
            
            elif command in VALID_IPS:
                responseMessage = "Error: No command found."

            else:
                responseMessage = "Error: Unknown command or invalid format"

        # กรณีที่ 2: คำสั่งมี 3 ส่วน (e.g., /... 10.0.15.61 create)
        elif num_parts == 3:
            target_ip = parts[1]
            command = parts[2]

            if not method_is_set:
                responseMessage = "Error: No method specified"
            elif target_ip not in VALID_IPS:
                responseMessage = "Error: Invalid IP address specified."
            elif command not in PART1_COMMANDS:
                 responseMessage = f"Error: Unknown command '{command}'"
            else:
                method = user_sessions[MY_STUDENT_ID]["method"]
                module = restconf_final if method == "restconf" else netconf_final
                func_to_call = getattr(module, command)
                responseMessage = func_to_call(MY_STUDENT_ID, target_ip)

        else:
            if message != f"/{MY_STUDENT_ID}":
                 responseMessage = "Error: Invalid command format."
        # --- END: 2025 New Command Parsing Logic (Refined) ---

        # ส่วนของการส่งข้อความกลับ
        if responseMessage:
            if command == "showrun" and responseMessage == 'ok':
                with open(filename, 'rb') as fileobject:
                    payload = {"roomId": ROOM_ID, "text": "show running config", "files": (filename, fileobject, "text/plain")}
                    postData = MultipartEncoder(fields=payload)
                    HTTPHeaders = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": postData.content_type}
            else:
                payload = {"roomId": ROOM_ID, "text": responseMessage}
                postData = json.dumps(payload)
                HTTPHeaders = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}   

            try:
                r_post = requests.post("https://webexapis.com/v1/messages", data=postData, headers=HTTPHeaders)
                r_post.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error sending message: {e}")