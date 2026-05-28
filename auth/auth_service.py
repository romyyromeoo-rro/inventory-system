import hashlib
import time
import bcrypt
from datetime import datetime, timedelta
from security import *
from auth.password_security import *
from auth.token_service import *
from core.config import config
from security.rate_limiter import is_rate_limited


SECRET_KEY = config.SECRET_KEY



def create_user(conn):
    username = input("Username Baru:  ")
    password = input("Password:  ")
    role = input("Role (admin/staff):")

    hashed = hash_password(password)
    cursor = conn.cursor()

    try:
        cursor.execute("""INSERT INTO users
         (username, password, role, salt)
         VALUES (?, ?, ?, ?)""", (username, hashed, role, salt))
        conn.commit()
        print("User Berhasil Dibuat!!")

    except:
        print("Username Sudah Ada.")




def login_user(conn, username, password, ip_address=None):
    if not username or not password.strip():
        return None, None, "Invalid username or password!"

    cursor = conn.cursor()

    cursor.execute("""SELECT password,
     role, failed_attempts, locked_until,
     salt FROM users WHERE username=?""", (username,))

    result = cursor.fetchone()

    if not result:
        return None, None, "Invalid username or password"

    user = dict(result)

    db_password = user["password"]
    role = user["role"]

    if verify_password(password, db_password):
        security_log(f"LOGIN SUCCSES {username}", ip_address)
        return username, role, "Login Success"


    else:
        security_log(f"LOGIN FAILED {username}", ip_address)
        return None, None, "Invalid username or password"


def login(conn):
    username = input("Username: ")
    password = input("Password: ")

    user, role, message = login_user(conn, username, password)

    print(message)
    print("LOGIN FLOW: kena Fallback (error)")
    return user, role
