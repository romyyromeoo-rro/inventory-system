from fastapi import FastAPI
from api.monitoring_api import router as monitoring_router
from api.inventory_api import router as inventory_router
from database import get_connection
from auth.auth_service import *
from inventory_manager import *
from services.audit_service import log_action_service
from services.metrics import get_metrics
from menu import show_menu
from datetime import datetime
from security import *


session = None

app = FastAPI()

app.include_router(inventory_router)
app.include_router(monitoring_router)

def create_app():
    app = FastAPI()
    app.include_router(inventory_router)
    app.include_router(monitoring_router)
    return app


app = create_app()



@app.post("/login")
def login_api(username: str, password: str):
    conn = get_connection()
    user, role, message = login_user(conn, username, password)

    if not user:
        return {"status": "error", "message": message}

    return {
        "status": "Success",
        "username": user,
        "role": role
    }

@app.get("/metrics")
def metrics():
    return get_metrics()



def main():
    conn = get_connection()

    current_user, role = login(conn)

    if current_user:
        session = {
            "username": current_user,
            "role": role,
            "last_activity": datetime.now(),
            "token": create_jwt(current_user, role)
        }
        print(f"🔑 Token: {session['token']}")
    else:
        print("Access Denied.")
        return


    check_low_stock(conn)
    show_menu(conn, session)

if __name__ == "__main__":
    main()






