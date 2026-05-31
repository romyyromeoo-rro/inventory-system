from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from app.databased import get_db
from app.models.inventory import InventoryItem
from services.inventory_service import *
from auth.permissions import *
from auth.auth_service import *
from auth.token_service import *
from security.rate_limiter import is_rate_limited
from schema import *
from typing import Optional
from auth.dependencies import *
from fastapi.security import OAuth2PasswordRequestForm



router = APIRouter()




@router.get("/protected")
def protected(user=Depends(get_current_user)):                                              return {"message": "Access Granted", "user": user}




@router.post("/login")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_connection()
    ip = request.client.host

    username = form_data.username
    password = form_data.password

    ip_key = f"ip:{ip}"
    user_key = f"login:{username}"

    if is_rate_limited(ip_key, limit=10, window=600):
        raise HTTPException(status_code=429, detail="Too many request from this IP")

    if is_rate_limited(user_key, limit=10, window=600):
            raise HTTPException(429, "Too many login attempts")

    user, role, message = login_user(conn, username, password, ip)

    if not user:
        security_log(f"FAILED LOGIN {username}", ip)

        raise HTTPException(status_code=401, detail=message)

    security_log(f"LOGIN SUCCESS {username}", ip)

    payload = {                                                                                 "sub": user,
        "sub": username,
        "role": role
    }

    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    print("🔥 LOGIN END")

    return {
       "access_token": access_token,
       "refresh_token": refresh_token,
       "token_type": "bearer"
    }




@router.post("/refresh")
def refresh_token(refresh_token: str):
    if is_token_blacklisted(
        refresh_token
    ):
        raise HTTPException(
            401,
            "Refresh Token Revoked"
        )

    payload = verify_token(refresh_token)

    if payload is None:
        raise HTTPException(401, "Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(401, "Not a refresh token")

    blacklist_token(
        refresh_token,
        payload["exp"]
    )

    new_payload = {
        "sub": payload["sub"],
        "role": payload["role"]
    }

    new_access_token = create_access_token(new_payload)
    new_refresh = create_refresh_token(new_payload)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }




@router.post("/logout")
def logout(token: str=Depends(oauth2_scheme)):
    payload = verify_token(token)

    jti = payload.get("jti")
    exp = payload.get("exp")

    if not jti:
        raise HTTPException(400, "Invalid token")

    blacklist_token(jti, exp)

    return {"message": "Logged out successfully"}




@router.get("/items")
def get_items(
request: Request):
#user=Depends(get_current_user)):
    ip = request.client.host
    key = f"{ip}:/items"

    if is_rate_limited(key, limit=5, window=60):
        raise HTTPException(429, "Too many request")

    conn = get_connection()
    item = get_item_service()

    return {"items": item}





@router.get("/items/{id}", response_model=SingleItemResponse)
def get_item(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        return get_item_by_id_service(
            db,
            id
        )

    except Exception as e:
        raise HTTPException(404, str(e))



@router.post("/items")
def create_item(
    new_item: ItemsCreate,
    request: Request,
    db: Session = Depends(get_db),
user=Depends(require_permission("create"))):
    try:
        return create_item_service(
            db,
            new_item,
            request
        )

    except Exception as e:
        raise HTTPException(400, str(e))




@router.put("/items/{id}")
def update_item(
    id: int,
    new_data: ItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
user=Depends(require_permission("update"))):

    ip = request.client.host

    if is_rate_limited(f"{ip}:/items/{id}", limit=3, window=300):
        raise HTTPException(429, "Too many request")

    try:
        result = update_item_service(
            db,
            id,
            new_data,
            request
        )

        return result

    except Exception as e:
        raise HTTPException(400, str(e))



@router.delete("/items/{id}", response_model=DeleteResponse)
def delete_item(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
user=Depends(require_permission("delete"))):

    ip = request.client.host

    if is_rate_limited(f"{ip}:/items/{id}", limit=3, window=300):
        raise HTTPException(429, "Too many requests")

    try:
        result = delete_item_service(db, id, request)
        return result

    except Exception as e:
        raise HTTPException(400, str(e))

