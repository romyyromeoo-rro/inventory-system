from starlette.middleware.base import BaseHTTPMiddleware 
from fastapi.responses import JSONResponse
from security import *
from task_queue import push_log
from fastapi import Request, HTTPException



EXCLUDED_PATHS = ["/docs", "/openapi.json"]
IMPORTANT_METHODS = ["POST", "PUT", "DELETE"]



class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host
        endpoint = request.url.path
        method = request.method

        print("🌍 REQUEST MASUK:", method, endpoint)


        response = await call_next(request)

        if endpoint == "/login":
            return response

        elif endpoint.startswith("/items"):
            return response

        elif endpoint in EXCLUDED_PATHS:
            return response

        elif method not in IMPORTANT_METHODS:
            return response



        try:
            auth_header = request.headers.get("Authorization")
            username = "anonymous"
            payload = None

            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                payload = verify_token(token)

                if payload:
                    username = payload.get("sub")

            push_log({
              "username"  : username,
              "action"    : f"{method} {endpoint}",
              "ip_address": ip,
              "endpoint"  : endpoint
            })


        except Exception as e:
            print("LOG ERROR:", e)
        return response




class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print("🌐 REQUEST:", request.method, request.url.path)

        ip = request.client.host
        endpoint = request.url.path

        limit = 20
        window = 60

        if endpoint in ["/docs", "/openapi.json", "/login"]:
            return await call_next(request)

        if is_rate_limited(ip, endpoint, limit, window):
            return JSONResponse(status_code=429, content={"detail": "Too many request"})

        return await call_next(request)
