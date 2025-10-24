#######################################################################################
# Yourname:
# Your student ID:
# Your GitHub Repo: 

#######################################################################################
# 1. Import libraries for API requests, JSON formatting, time, os, (restconf_final or netconf_final), netmiko_final, and ansible_final.
import os
import requests
import json
import time
from requests_toolbelt.multipart.encoder import MultipartEncoder

# เลือก import แค่ตัวเดียวระหว่าง restconf_final หรือ netconf_final
import restconf_final 
# import netconf_final 

import netmiko_final
import ansible_final

#######################################################################################
# 2. Assign the Webex access token to the variable ACCESS_TOKEN using environment variables.

ACCESS_TOKEN = os.environ.get("WEBEX_ACCESS_TOKEN")

#######################################################################################
# 3. Prepare parameters get the latest message for messages API.

# Defines a variable that will hold the roomId
roomIdToGetMessages = (
    # "IPA CRASH-ROOM OF 66070139"
    "Y2lzY29zcGFyazovL3VybjpURUFNOnVzLXdlc3QtMl9yL1JPT00vNjgyY2JkNTAtNmM2My0xMWYwLThlOWMtZTc0YzljNTJiNTY5"
)

while True:
    # always add 1 second of delay to the loop to not go over a rate limit of API calls
    time.sleep(1)

    # the Webex Teams GET parameters
    #  "roomId" is the ID of the selected room
    #  "max": 1  limits to get only the very last message in the room
    getParameters = {"roomId": roomIdToGetMessages, "max": 1}

    # the Webex Teams HTTP header, including the Authoriztion
    getHTTPHeader = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

# 4. Provide the URL to the Webex Teams messages API, and extract location from the received message.
    my_student_id = "66070139"
    # Send a GET request to the Webex Teams messages API.
    # - Use the GetParameters to get only the latest message.
    # - Store the message in the "r" variable.
    r = requests.get(
        "https://webexapis.com/v1/messages",
        params=getParameters,
        headers=getHTTPHeader,
    )
    # verify if the retuned HTTP status code is 200/OK
    if not r.status_code == 200:
        raise Exception(
            "Incorrect reply from Webex Teams API. Status code: {}".format(r.status_code)
        )

    # get the JSON formatted returned data
    json_data = r.json()

    # check if there are any messages in the "items" array
    if len(json_data["items"]) == 0:
        raise Exception("There are no messages in the room.")

    # store the array of messages
    messages = json_data["items"]
    
    # store the text of the first message in the array
    message = messages[0]["text"]
    print("Received message: " + message)

    # check if the text of the message starts with the magic character "/" followed by your studentID and a space and followed by a command name
    #  e.g.  "/66070123 create"
    if message.startswith(f"/{my_student_id}"):

        # extract the command
        # split the message by spaces and get the second element (index 1)
        command = message.split()[1]
        print(command)

# 5. Complete the logic for each command
        
        # Initialize filename to None for other commands
        filename = None 
        
        if command == "create":
            responseMessage = restconf_final.create(my_student_id)
        elif command == "delete":
            responseMessage = restconf_final.delete(my_student_id)
        elif command == "enable":
            responseMessage = restconf_final.enable(my_student_id)
        elif command == "disable":
            responseMessage = restconf_final.disable(my_student_id)
        elif command == "status":
            responseMessage = restconf_final.status(my_student_id)
        elif command == "gigabit_status":
            responseMessage = netmiko_final.gigabit_status()
        elif command == "showrun":
            # Assuming a router name from the lab, e.g., 'CSR1KV-Pod1-1'
            # You might need to adjust this based on your specific router.
            router_name = 'CSR1KV-Pod1-1'
            responseMessage, filename = ansible_final.showrun(my_student_id, router_name)
        else:
            responseMessage = "Error: No command or unknown command"
# 6. Complete the code to post the message to the Webex Teams room.

        # ... (code from section 5) ...

        if command == "showrun" and responseMessage == 'ok':
            # This block handles file attachment for a successful showrun
            fileobject = open(filename, 'rb')
            filetype = "text/plain"
            
            payload = {
                "roomId": roomIdToGetMessages,
                "text": "show running config",
                "files": (filename, fileobject, filetype),
            }
            postData = MultipartEncoder(fields=payload)
            
            HTTPHeaders = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": postData.content_type,
            }
        else:
            # This block handles all other commands which send only text
            payload = {"roomId": roomIdToGetMessages, "text": responseMessage}
            postData = json.dumps(payload)

            HTTPHeaders = {
                "Authorization": f"Bearer {ACCESS_TOKEN}", 
                "Content-Type": "application/json"
            }   

        # Post the call to the Webex Teams message API.
        r = requests.post(
            "https://webexapis.com/v1/messages",
            data=postData,
            headers=HTTPHeaders,
        )
        if not r.status_code == 200:
            raise Exception(
                "Incorrect reply from Webex Teams API. Status code: {}. Text: {}".format(r.status_code, r.text)
            )
