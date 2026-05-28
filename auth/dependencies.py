from fastapi.security import OAuth2PasswordBearer
from fastapi import FastAPI, HTTPException, Depends
from auth.token_service import *


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")



def get_current_user(token: str = Depends(oauth2_scheme)):
    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token revoked. Please login again.")


    print("DEBUG:", token)

    payload = verify_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload


