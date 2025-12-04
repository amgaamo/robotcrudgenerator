# modules/license_checker.py
import datetime
import json
import os
from cryptography.fernet import Fernet

# 1. ต้องใช้ Key ตัวเดียวกับตอนสร้าง (Copy มาใส่ตรงนี้เลย)
SECRET_KEY = b'nXF3_M2mlDrZ1ZPRvibUD_F9eY0wG97_yge2-orjgSc=' 

def check_license_file(key_path="license.key"):
    if not os.path.exists(key_path):
        return False, "License file not found.", None # <--- เพิ่ม None

    try:
        with open(key_path, "rb") as file:
            encrypted_data = file.read()
        
        f = Fernet(SECRET_KEY)
        decrypted_data = f.decrypt(encrypted_data)
        data = json.loads(decrypted_data.decode())
        
        expiration_str = data.get("expiration_date")
        expiration_date = datetime.datetime.strptime(expiration_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        
        if today > expiration_date:
            # ส่งวันที่กลับไปด้วย แม้จะหมดอายุแล้ว
            return False, f"Expired since {expiration_str}", expiration_date
            
        # ✅ ส่งวันที่กลับไปด้วย (ตัวที่ 3)
        return True, "Valid", expiration_date

    except Exception:
        return False, "Invalid license file.", None