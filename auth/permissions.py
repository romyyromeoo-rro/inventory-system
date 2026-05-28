from fastapi import HTTPException, Depends
from auth.dependencies import get_current_user



permission_map = {
    "admin": {
        "create", "read", "update", "delete"
    },

    "staff": {
        "read"
    }
}




def require_permission(permission: str):
    def checker(user = Depends(get_current_user)):
        role = user.get("role")

        if role not in permission_map:
            raise HTTPException(status_code=403, detail="Role not recognized")

        if permission not in permission_map[role]:
            raise HTTPException(status_code=403, detail="Permission denied")

        return user

    return checker

