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

# --- Initialization ---
load_dotenv()

import restconf_final 
import netconf_final 
import netmiko_final
import ansible_final

# --- Configuration Loading ---
ACCESS_TOKEN = os.environ.get("WEBEX_ACCESS_TOKEN")
ROOM_ID = os.environ.get("WEBEX_ROOM_ID")
MY_STUDENT_ID = os.environ.get("MY_STUDENT_ID")

if not all([ACCESS_TOKEN, ROOM_ID, MY_STUDENT_ID]):
    raise Exception("\n!!! กรุณาสร้างไฟล์ .env และใส่ค่าให้ครบถ้วน !!!\n"
                    "WEBEX_ACCESS_TOKEN, WEBEX_ROOM_ID, MY_STUDENT_ID")

# --- Global State and Constants ---
user_sessions = {} 
VALID_IPS = ["10.0.15.61", "10.0.15.62", "10.0.15.63", "10.0.15.64", "10.0.15.65"]
PART1_COMMANDS = ["create", "delete", "enable", "disable", "status"]
MOTD_COMMAND = "motd"
SHOWRUN_COMMAND = "showrun"
GIGABIT_STATUS_COMMAND = "gigabit_status"

# --- Main Application Loop ---
while True:
    # time.sleep(1)
    
    # Fetch the latest message from Webex
    try:
        getParameters = {"roomId": ROOM_ID, "max": 1}
        getHTTPHeader = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        r = requests.get("https://webexapis.com/v1/messages", params=getParameters, headers=getHTTPHeader)
        r.raise_for_status()
        json_data = r.json()
        if not json_data["items"]: 
            continue
    except requests.exceptions.RequestException as e:
        print(f"Error fetching messages: {e}")
        continue
    
    message = json_data["items"][0]["text"]
    print(f"Received message: \"{message}\"")

    if message.startswith(f"/{MY_STUDENT_ID}"):
        parts = message.split()
        num_parts = len(parts)
        
        responseMessage, filename, command = "", None, ""

        if num_parts < 2: 
            continue

        # --- Final Command Parsing Logic ---
        ip_address, main_command = None, None
        
        # ระบุตำแหน่งที่เป็นไปได้ของ IP และ Command
        # Case: /... <ip> <command> ...
        if num_parts >= 3 and parts[1] in VALID_IPS:
            ip_address = parts[1]
            main_command = parts[2]
        # Case: /... <command>
        elif num_parts == 2:
            main_command = parts[1]
        
        # --- เริ่มตัดสินใจจาก main_command ---
        if main_command in ["restconf", "netconf"]:
            user_sessions[MY_STUDENT_ID] = {"method": main_command}
            responseMessage = f"Ok: {main_command.capitalize()}"

        elif main_command in PART1_COMMANDS:
            if MY_STUDENT_ID not in user_sessions:
                responseMessage = "Error: No method specified"
            elif not ip_address:
                responseMessage = "Error: No IP specified"
            else:
                method = user_sessions[MY_STUDENT_ID]["method"]
                module = restconf_final if method == "restconf" else netconf_final
                func_to_call = getattr(module, main_command)
                responseMessage = func_to_call(MY_STUDENT_ID, ip_address)

        elif main_command == MOTD_COMMAND:
            if not ip_address:
                responseMessage = "Error: No IP specified"
            elif ip_address not in VALID_IPS:
                responseMessage = "Error: No MOTD Configured" # ตามโจทย์พิเศษ
            else:
                if num_parts == 3:
                    responseMessage = netmiko_final.get_motd(ip_address)
                else:
                    motd_message = " ".join(parts[3:])
                    responseMessage = ansible_final.set_motd(ip_address, motd_message)

        # --- START: การเปลี่ยนแปลงสำหรับ gigabit_status ---
        elif main_command == GIGABIT_STATUS_COMMAND:
            if not ip_address:
                responseMessage = "Error: No IP specified"
            else:
                # ส่ง IP ที่ได้รับมาเข้าไปในฟังก์ชัน
                responseMessage = netmiko_final.gigabit_status(ip_address)
        # --- END: การเปลี่ยนแปลง ---
        
        elif main_command == SHOWRUN_COMMAND:
            if not ip_address:
                responseMessage = "Error: No IP specified"
            else:
                command = SHOWRUN_COMMAND
                responseMessage, filename = ansible_final.showrun(MY_STUDENT_ID, ip_address)
        
        else:
             if ip_address and not main_command:
                  responseMessage = "Error: No command found."
             else:
                  responseMessage = "Error: Unknown command or invalid format"


        # --- Send Response to Webex ---
        if responseMessage:
            # กำหนดค่าเริ่มต้นสำหรับ postData และ HTTPHeaders
            postData = None
            HTTPHeaders = None

            if command == SHOWRUN_COMMAND and responseMessage == 'ok':
                try:
                    # เปิดไฟล์และส่ง request ภายใน with block เดียวกัน
                    with open(filename, 'rb') as fileobject:
                        payload = {
                            "roomId": ROOM_ID,
                            "text": "show running config",
                            "files": (os.path.basename(filename), fileobject, "text/plain")
                        }
                        # เตรียมข้อมูลที่จะส่ง
                        postData = MultipartEncoder(fields=payload)
                        # เตรียม Headers
                        HTTPHeaders = {
                            "Authorization": f"Bearer {ACCESS_TOKEN}",
                            "Content-Type": postData.content_type
                        }
                        
                        # --- ย้ายคำสั่งส่ง request มาไว้ตรงนี้ ---
                        print("Sending showrun file to Webex...")
                        r_post = requests.post("https://webexapis.com/v1/messages", data=postData, headers=HTTPHeaders)
                        r_post.raise_for_status()
                        print("File sent successfully.")

                except FileNotFoundError:
                    print(f"ERROR: File '{filename}' not found after Ansible run.")
                    responseMessage = "Error: Could not find the generated config file."
                    # ถ้าหาไฟล์ไม่เจอ ให้ไปสร้าง payload สำหรับส่งข้อความ Error แทน
                    payload = {"roomId": ROOM_ID, "text": responseMessage}
                    postData = json.dumps(payload)
                    HTTPHeaders = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
                    # ส่งข้อความ Error
                    requests.post("https://webexapis.com/v1/messages", data=postData, headers=HTTPHeaders)
                except requests.exceptions.RequestException as e:
                    print(f"Error sending file message: {e}")

            # กรณีอื่นๆ (ข้อความธรรมดา)
            else:
                payload = {"roomId": ROOM_ID, "text": responseMessage}
                postData = json.dumps(payload)
                HTTPHeaders = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
                
                try:
                    r_post = requests.post("https://webexapis.com/v1/messages", data=postData, headers=HTTPHeaders)
                    r_post.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(f"Error sending text message: {e}")