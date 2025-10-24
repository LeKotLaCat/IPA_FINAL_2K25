import subprocess
import os
from dotenv import load_dotenv

load_dotenv()
ROUTER_USER = os.environ.get("ROUTER_USER", "admin")
ROUTER_PASS = os.environ.get("ROUTER_PASS", "cisco")

def _run_ansible_playbook(playbook_file, target_ip, extra_vars_dict):
    """
    Helper function กลางสำหรับรัน Ansible Playbook แบบ Dynamic
    รับ extra_vars เป็น dictionary เพื่อความปลอดภัยและยืดหยุ่น
    """
    # สร้าง string ของ extra_vars จาก dictionary
    extra_vars_str = " ".join([f"{key}='{value}'" for key, value in extra_vars_dict.items()])
    
    # เพิ่มค่าพื้นฐานที่จำเป็นเสมอ
    base_vars = f"ansible_user={ROUTER_USER} ansible_password={ROUTER_PASS} ansible_network_os=ios ansible_connection=network_cli"
    
    command = [
        'ansible-playbook',
        playbook_file,
        '-i', f"{target_ip},",
        '--extra-vars',
        f"{base_vars} {extra_vars_str}"
    ]
    
    env = os.environ.copy()
    env['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
    env['ANSIBLE_TIMEOUT'] = '60'               
    
    print(f"Running Ansible command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, env=env)
    
    print(f"----- Ansible Output ({playbook_file}) -----")
    print(result.stdout)
    if result.stderr:
        print("----- Ansible STDERR -----")
        print(result.stderr)
    print("-------------------------------------")
    
    return result.stdout

def showrun(student_id, target_ip):
    """
    ฟังก์ชัน showrun ที่เรียกใช้ playbook_showrun.yaml
    """
    filename = f"show_run_{student_id}_{target_ip}.txt"
    
    # ส่งตัวแปรที่ playbook นี้ต้องการเท่านั้น
    extra_vars = {
        "student_id": student_id,
        "ansible_host": target_ip # playbook_showrun ใช้ตัวนี้สร้างชื่อไฟล์
    }
    
    output = _run_ansible_playbook(
        playbook_file='playbook_showrun.yaml',
        target_ip=target_ip,
        extra_vars_dict=extra_vars
    )
    
    if 'ok=2' in output and 'failed=0' in output:
        return "ok", filename
    else:
        return "Error: Ansible", None

def set_motd(target_ip, motd_message):
    """
    ฟังก์ชัน set_motd ที่เรียกใช้ playbook_motd.yaml
    """
    # ส่งตัวแปรที่ playbook นี้ต้องการเท่านั้น
    extra_vars = {
        "motd_text": motd_message
    }

    output = _run_ansible_playbook(
        playbook_file='playbook_motd.yaml',
        target_ip=target_ip,
        extra_vars_dict=extra_vars
    )
    
    if 'changed=1' in output and 'failed=0' in output:
        return "Ok: success"
    else:
        return "Error: Failed to set MOTD via Ansible"