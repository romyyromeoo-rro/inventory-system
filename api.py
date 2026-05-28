from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm
from middleware import *
from roles import admin_required, require_permission
from fastapi import FastAPI, Depends, Request, HTTPException, Query
from database import get_connection
from auth import login_user
from security import *
from inventory_manager import views_items
from dependencies import *
from schema import ItemUpdate
from redis_client import redis_client
from task_queue import push_log
import time


app = FastAPI()
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditMiddleware)

LAST_UPDATE = {}

@app.get("/")
def root():
    return {"message": "Api jalan 🔥"}



#@app.get("/admin")
#def admin_only(user=Depends(get_current_user)):
#    admin_required(user)
#    return {"message": "Welcome Admin"}



@app.get("/protected")
def protected(user=Depends(get_current_user)):
    return {"message": "Access Granted", "user": user}




@app.post("/login")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_connection()
    ip = request.client.host

    username = form_data.username
    password = form_data.password


    print("🔥 LOGIN HIT", time.time())

    if is_rate_limited(ip, "/login", limit=5, window_minutes=1):
        raise HTTPException(status_code=429, detail="Too many login attempts")


    if is_ip_blocked(ip):
        raise HTTPException(status_code=403, detail="IP blocked. Try Later.")

    user, role, message = login_user(conn, username, password)

    if not user:
        attempts = count_failed_attempts(ip)
        security_log(f"FAILED LOGIN {username}", ip)

        if attempts >= 3:
            block_ip(ip, minutes=1)
            security_log(f"IP BLOCKED {username}", ip)

        raise HTTPException(status_code=401, detail=message)



    if ip in ip_attempts:
        del ip_attempts[ip]

    security_log(f"LOGIN SUCCESS {username}", ip)

    payload = {
        "sub": user,
        "role": role
    }

    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    print("🔥 LOGIN END")

    return {
       "access_token": access_token,
       "refresh_token": refresh_token,
       "token_type": "bearer",
       "message": message
    }


@app.post("/refresh")
def refresh_token(refresh_token: str):
    payload = verify_token(refresh_token)

    if payload is None:
        raise HTTPException(401, "Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(401, "Not a refresh token")

    new_payload = {
        "sub": payload["sub"],
        "role": payload["role"]
    }

    new_access_token = create_access_token(new_payload)

    return {"access_token": new_access_token}




@app.post("/logout")
def logout(token: str=Depends(oauth2_scheme)):
    payload = verify_token(token)

    if not payload:
        raise HTTPException(401, "Invalid token")

    exp = payload.get("exp")

    if exp is None:
        raise HTTPException(400, "Token missing exp")

    blacklist_token(token, exp)
    return {"message": "Logged out successfully"}




@app.get("/items")
def get_items(
    request: Request,
    user=Depends(get_current_user)):
        cache_key = "Items_list"

        cached_data = redis_client.get(cache_key)

        if cached_data:
            print("⚡ FROM CACHE")
            return {"items": json.loads(cached_data)}

        ip = request.client.host
        endpoint = "/items"

        if is_rate_limited(ip, "/items", limit=5, window_minutes=1):
            raise HTTPException(status_code=429, detail="Too many request")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""SELECT id, name, stock
        FROM items""")

        rows = cursor.fetchall()
        conn.close


        items = []
        for row in rows:
            items.append({
                "id": row[0],
                "name": row[1],
                "stock": row[2]
            })

        redis_client.setex(cache_key, 60, json.dumps(items))

        print("🐢 FROM DB")
        return {"items": items}



@app.put("/items/{id}")
def update_item(
    id: int,
    new_data: ItemUpdate,
    request: Request,
user=Depends(require_permission("admin"))):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT name, stock FROM items
        WHERE id = ?""", (id,))

    item = cursor.fetchone()

    if not item:
        raise HTTPException(404, "Item not found")

    key = f"{user['sub']}_{id}"
    now = time.time()

    if key in LAST_UPDATE and now - LAST_UPDATE[key] < 2:
        raise HTTPException(429, "Too fast")

    LAST_UPDATE[key] = now

    old_name = item[0]
    old_stock = item[1]

    new_name = new_data.name if new_data.name is not None else old_name
    new_stock = new_data.stock if new_data.stock is not None else old_stock

    if new_stock == old_stock and new_name == old_name:
        return {"message: No changes"}

    cursor.execute("""UPDATE items SET name = ?,
        stock = ? WHERE id = ?""", (new_name, new_stock, id))

    redis_client.delete("items_list")

    conn.commit()

    ip = request.client.host

    if is_rate_limited(ip, f"/items/{id}", limit=3, window_minutes=5):
        raise HTTPException(429, "Too many request")

    endpoint = str(request.url)

    push_log({
        "username"  : user["sub"],
        "action"    : "UPDATE_ITEM",
        "item_id"   : id,
        "item_name" : new_name,
        "old_stock" : old_stock,
        "new_stock" : new_stock,
        "ip_address": ip,
        "endpoint"  : endpoint
    })

    print("🔥 UPDATE HIT", time.time())

    conn.close()

    return {
        "message": "Item updated",
        "old_stock": old_stock,
        "new_stock": new_stock
    }



@app.delete("/items/{id}")
def delete_item(
    id: int,
    request: Request,
    user=Depends(require_permission("admin"))
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(""" SELECT name, stock FROM items
        WHERE id = ?""", (id,))

    item = cursor.fetchone()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item_name = item[0]
    old_stock = item[1]

    cursor.execute("DELETE FROM items WHERE id = ?", (id,))

    redis_client.delete("items_list")

    conn.commit()
    conn.close()

    push_log({
        "username"  : user["sub"],
        "action"    : "DELETE_ITEM",
        "item_id"   : id,
        "item_name" : item_name,
        "old_stock" : old_stock,
        "new_stock" : 0,
        "change"    : 0 - old_stock,
        "ip_address": request.client.host,
        "endpoint"  : str(request.url)
    })


    return {"message": "Deleted by admin"}



@app.get("/audit_logs")
def get_logs(
    username: str = Query(None),
    action: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(5, ge=1, le=50),
user=Depends(require_permission("admin"))):

    conn = get_connection()
    cursor = conn.cursor()

    query = """ SELECT id, username, action,
    item_id, item_name, old_stock, new_stock,
    change, ip_address, endpoint, timestamp
    FROM audit_log WHERE 1=1"""

    params = []

    if username:
        query += " AND username = ?"
        params.append(username)

    if action:
        query += " AND action LIKE ?"
        params.append(f"%{action}%")

    offset = (page - 1) * limit
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    logs = []
    for row in rows:
        logs.append({
            "id": row[0],
            "username": row[1],
            "action": row[2],
            "item_id": row[3],
            "item_name": row[4],
            "old_stock": row[5],
            "new_stock": row[6],
            "change": row[7],
            "ip_address": row[8],
            "endpoint": row[9],
            "timestamp": row[10]
        })

        return {"logs": logs}




