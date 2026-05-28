from fastapi import HTTPException
from services.audit_service import log_action_service


def save_log_to_db(**kwargs):
    raise Exception("DEPRECATED: gunakan log_action_service")






