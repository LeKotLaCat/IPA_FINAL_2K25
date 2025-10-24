#######################################################################################
# Name: PETCHPRAETHONG INUTHAI
# student ID: 66070139
# GitHub Repo: https://github.com/LeKotLaCat/IPA_FINAL_2K25.git
#######################################################################################

import subprocess

# ฟังก์ชันนี้ต้องรับ student_id และ router_name มาจากไฟล์หลัก
# เพื่อสร้างชื่อไฟล์และส่งเป็นตัวแปรให้ playbook
def showrun(student_id, router_name):
    # read https://www.datacamp.com/tutorial/python-subprocess to learn more about subprocess

    # สร้างชื่อไฟล์ที่เราคาดหวังว่าจะได้จาก playbook
    filename = f"show_run_{student_id}_{router_name}.txt"
    
    # ประกอบร่างคำสั่ง ansible-playbook ให้สมบูรณ์
    # -i hosts: ระบุ inventory file
    # --extra-vars: ส่งตัวแปรจาก Python เข้าไปใน playbook
    command = [
        'ansible-playbook',
        'playbook.yaml',
        '-i', 'hosts',
        '--extra-vars', f"student_id={student_id} router_name={router_name}"
    ]

    # รันคำสั่ง
    result = subprocess.run(command, capture_output=True, text=True)
    
    # เก็บผลลัพธ์ stdout เพื่อนำมาตรวจสอบ
    ansible_output = result.stdout
    print("----- Ansible Output -----")
    print(ansible_output)
    print("--------------------------")

    # ตรวจสอบผลลัพธ์: 'ok=2' หมายถึง 2 tasks สำเร็จ และ 'failed=0' คือไม่มี task ไหนล้มเหลว
    if 'ok=2' in ansible_output and 'failed=0' in ansible_output:
        # ถ้าสำเร็จ คืนค่า 'ok' และชื่อไฟล์ที่สร้างขึ้น
        return "ok", filename
    else:
        # ถ้าล้มเหลว คืนค่า Error และ None สำหรับชื่อไฟล์
        return "Error: Ansible", None