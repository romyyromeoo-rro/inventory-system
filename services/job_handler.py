from core.exceptions import InvalidPayloadError
from services.audit_service import log_action_service
from database import get_connection



def handle_log_action(job):
    payload = job["payload"]

    if not payload.get("username") or not payload.get("action"):
        raise InvalidPayloadError("Invalid payload")

    conn = get_connection()

    try:
        log_action_service(
            conn,
            username=payload.get("username"),
            action=payload.get("action"),
            item_id=payload.get("item_id"),
            item_name=payload.get("item_name"),
            old_stock=payload.get("old_stock"),
            new_stock=payload.get("new_stock"),
            ip_address=payload.get("ip_address"),
            endpoint=payload.get("endpoint")
        )
    except Exception as e:
        print("❌ Handle error:", e)
        raise

    finally:
        conn.close()
