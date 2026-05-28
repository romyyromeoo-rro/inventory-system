from database import get_connection
from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt
import secrets
import hashlib
import time
import base64
import json
import hmac

LOCK_DURATION = 60
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10
BLOCK_TIME = 60


ip_attempts = {}
blocked_ips = {}


def is_ip_blocked(ip):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT blocked_until FROM blocked_ips
        WHERE ip_address = ?""", (ip,)
    )

    result = cursor.fetchone()
    if not result:
        conn.close()
        return False

    blocked_until = result[0]
    unlock_time = datetime.fromisoformat(blocked_until)

    if datetime.now() >= unlock_time:
        cursor.execute("""
            DELETE FROM blocked_ips
            WHERE ip_address = ?""", (ip,)
        )

        conn.commit()
        conn.close()
        return False

    conn.close()
    return True




def track_ip(ip):
    if ip not in ip_attempts:
        ip_attempts[ip] = 0

    ip_attempts[ip] += 1
    return ip_attempts[ip]



def block_ip(ip):
    conn = get_connection()
    cursor = conn.cursor()

    blocked_until = (datetime.now() + timedelta(minutes=minutes)).isoformat()

    cursor.execute("""
        INSERT OR REPLACE INTO blocked_ips(
        ip_address, blocked_until) VALUES (?, ?)""", (ip, blocked_until))

    conn.commit()
    conn.close()


def count_failed_attempts(ip):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT (*) FROM audit_log WHERE
        ip_address = ? AND action = 'failed_login'
        AND timestamp >= datetime('now', '-1 minutes')""", (ip,))

    count = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return count



#def is_rate_limited(ip, endpoint, limit=60, window_minutes=30):
    #conn = get_connection()
    #cursor = conn.cursor()

    #cursor.execute(""
        #SELECT COUNT (*) FROM rate_limits
        #WHERE ip_address = ? AND endpoint = ?
        #AND timestamp >= datetime('now', ?)"", (ip, endpoint, f'-{window_minutes} minutes'))

    #count = cursor.fetchone()[0]

    #cursor.execute(""
        #INSERT INTO rate_limits (ip_address, endpoint)
        #VALUES (?, ?)"", (ip, endpoint))

    #conn.commit()
    #conn.close()

    return count >= limit




def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None



def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)




def blacklist_token(token: str, exp):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO token_blacklist
        (token, expired_at) VALUES (?, ?)
        """, (token, exp))

    conn.commit()
    conn.close()




def is_token_blacklisted(token: str):
    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT 1 FROM token_blacklist WHERE
        token = ?""", (token,))

    result = cursor.fetchone()
    conn.close()

    return result is not None



def verify_password(password, hashed):
    if isinstance(hashed, str):
        hashed = hashed.encode()

    return bcrypt.checkpw(
        password.encode(),
        hashed
    )



def base64_encode(data):
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def create_jwt(username, role):
    header = {"alg": "HS256", "typ": "JWT"}

    payload = {
        "username": username,
        "role": role,
        "exp": int(time.time()) + 300
    }

    header_enc = base64_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_enc = base64_encode(json.dumps(payload, separators=(",", ":")).encode())
    signature_raw = f"{header_enc}.{payload_enc}".encode()
    signature = hmac.new(
        SECRET_KEY.encode(),
        signature_raw,
        hashlib.sha256
    ).digest()

    signature_enc = base64_encode(signature)
    token = f"{header_enc}.{payload_enc}.{signature_enc}"
    return token


def base64_decode(data):
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)



def verify_jwt(token):
    try:
        header_enc, payload_enc, signature_enc = token.split(".")
        signature_raw = f"{header_enc}.{payload_enc}".encode()
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            signature_raw,
            hashlib.sha256
        ).digest()

        expected_signature_enc = base64_encode(expected_signature)

        if signature_enc != expected_signature_enc:
            return False

        payload = json.loads(base64_decode(payload_enc))

        if time.time() > payload["exp"]:
            print("⏳ Token Expired.")
            return False

        return payload

    except Exception:
        return False




def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()



def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())



def is_account_locked(locked_until):
    if not locked_until:
        return False

    try:
        unlock_time = datetime.fromisoformat(locked_until)
    except:
        return False

    return datetime.now() < unlock_time



def handle_failed_login(conn, username, failed_attempts):
    cursor = conn.cursor()
    failed_attempts += 1

    if failed_attempts >= 3:
        lock_time = datetime.now() + timedelta(seconds=LOCK_DURATION)

        cursor.execute("""
            UPDATE users SET failed_attempts = ?,
            locked_until = ? WHERE username=?""", (0, lock_time.isoformat(), username))
        print("Account Locked For 60 Seconds.")

        security_log(f"ACCOUNT LOCKED {username}")

    else:
        cursor.execute("""UPDATE users
            SET failed_attempts = ? WHERE username= ?""", (failed_attempts, username))
        print(f"❌ Login Failed ({failed_attempts}/3)")
        security_log(f"FAILED LOGIN {username} ({failed_attempts})")
    conn.commit()
    conn.close()


def reset_login_attempts(conn, username):
    cursor = conn.cursor()
    cursor.execute("""UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE username = ?""", (username,))
    conn.commit()
    conn.close()



def security_log(message, ip=None):
    time_now = datetime.now()
    log_line = f"[{time_now}]"

    if ip:
        log_line += f" [IP: {ip}]"

    log_line += f" {message}\n"

    with open("logs/security_log.txt", "a") as f:
        f.write(log_line)
