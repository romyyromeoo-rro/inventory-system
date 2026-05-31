from datetime import datetime, timedelta
from jose import jwt, JWTError
from database import get_connection
from fastapi import HTTPException
from core.config import config
import os
import uuid


SECRET_KEY = config.SECRET_KEY
ALGORITHM = config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES



def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM)



def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)

    jti = str(uuid.uuid4())

    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": jti
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )



def rotate_refresh_token(old_token: str):
    payload = verify_token(old_token)


    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid Token type")

    if not payload.get("sub"):
        raise HTTPException(401, "invalid Token Payload")

    jti = payload.get("jti")
    exp = payload.get("exp")

    if not jti:
        raise HTTPException(401, "Invalid token")

    blacklist_token(jti, exp)

    user_data = {
        "sub": payload.get("sub")
    }

    new_access = create_access_token(user_data)
    new_refresh = create_refresh_token(user_data)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh
    }



def verify_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        jti = payload.get("jti")

        if jti and is_token_blacklisted(jti):
            raise HTTPException(401, "Token Revoked")

        return payload

    except JWTError:
        raise HTTPException(401, "Invalid Token")




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



#def blacklist_token(jti: str, exp):
    #conn = get_connection()
    #cursor = conn.cursor()

    #cursor.execute(""
        #INSERT INTO token_blacklist
        #(jti, expired_at) VALUES (?, ?)
        #""", (jti, exp))

    #conn.commit()
    #conn.close()




#def is_token_blacklisted(jti: str):
    #conn = get_connection()
    #cursor = conn.cursor()


    #cursor.execute(""
        #SELECT 1 FROM token_blacklist WHERE
        #jti = ?""", (jti,))

    #result = cursor.fetchone()
    #conn.close()

    #return result is not None
