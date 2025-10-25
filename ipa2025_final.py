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
    time.sleep(1)
    
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

    # --- Start of Command Parsing Logic ---
    if message.startswith(f"/{MY_STUDENT_ID}"):
        parts = message.split()
        num_parts = len(parts)
        
        # Initialize variables for each loop iteration
        responseMessage = ""
        filename = None
        command = ""

        if num_parts < 2:
            continue # Ignore if only /studentID is sent

        # --- Flexible Command Parsing Logic ---
        
        # Case 1: Handle GIGABIT_STATUS (can appear anywhere after student ID)
        if GIGABIT_STATUS_COMMAND in parts:
            command = GIGABIT_STATUS_COMMAND
            responseMessage = netmiko_final.gigabit_status()
        
        # Case 2: Handle SHOWRUN (requires an IP)
        elif SHOWRUN_COMMAND in parts:
            command = SHOWRUN_COMMAND
            if num_parts < 3:
                responseMessage = "Error: No IP specified for showrun"
            else:
                target_ip = parts[1] # Assume IP is always the second part
                if target_ip not in VALID_IPS:
                    responseMessage = "Error: Invalid IP address specified."
                else:
                    responseMessage, filename = ansible_final.showrun(MY_STUDENT_ID, target_ip)

        # Case 3: Handle all other commands (Part 1 and MOTD)
        else:
            method_is_set = MY_STUDENT_ID in user_sessions
            
            # Subcase 3.1: Two-part commands (e.g., set method, or errors)
            if num_parts == 2:
                command = parts[1]
                if command in ["restconf", "netconf"]:
                    user_sessions[MY_STUDENT_ID] = {"method": command}
                    responseMessage = f"Ok: {command.capitalize()}"
                elif command in PART1_COMMANDS:
                    responseMessage = "Error: No method specified" if not method_is_set else "Error: No IP specified"
                elif command in VALID_IPS:
                    responseMessage = "Error: No command found."
                else:
                    responseMessage = "Error: Unknown command or invalid format"

            # Subcase 3.2: Three or more parts commands (Part 1 with IP, or MOTD)
            elif num_parts >= 3:
                target_ip = parts[1]
                command = parts[2]
                
                # --- START: New MOTD Logic ---
                # จัดการกับ MOTD เป็นกรณีพิเศษก่อน
                if command == MOTD_COMMAND:
                    # ถ้า IP ไม่ถูกต้อง หรือถ้า get_motd คืนค่า Error
                    # ให้ตอบกลับว่า "No MOTD Configured" ทั้งสองกรณี
                    if target_ip not in VALID_IPS:
                        responseMessage = "Error: No MOTD Configured"
                    else:
                        if num_parts == 3: # Get MOTD
                            responseMessage = netmiko_final.get_motd(target_ip)
                        else: # Set MOTD
                            motd_message = " ".join(parts[3:])
                            responseMessage = ansible_final.set_motd(target_ip, motd_message)

                # --- END: New MOTD Logic ---

                # --- Logic เดิมสำหรับ Part 1 และ SHOWRUN ---
                else: # ถ้าไม่ใช่คำสั่ง MOTD ให้ทำงานตาม Logic เดิม
                    if target_ip not in VALID_IPS:
                        responseMessage = "Error: Invalid IP address specified."
                    elif command in PART1_COMMANDS:
                        if num_parts != 3:
                            responseMessage = "Error: Invalid command format for Part 1 commands."
                        elif not method_is_set:
                            responseMessage = "Error: No method specified"
                        else:
                            method = user_sessions[MY_STUDENT_ID]["method"]
                            module = restconf_final if method == "restconf" else netconf_final
                            func_to_call = getattr(module, command)
                            responseMessage = func_to_call(MY_STUDENT_ID, target_ip)
                    elif command == SHOWRUN_COMMAND:
                        responseMessage, filename = ansible_final.showrun(MY_STUDENT_ID, target_ip)
                    else:
                        responseMessage = f"Error: Unknown command '{command}'"


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