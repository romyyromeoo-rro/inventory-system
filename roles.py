from fastapi import HTTPException
from fastapi import Depends
from dependencies import get_current_user

permission_map = {
    "admin": ["create", "read", "update", "delete"],
    "staff": ["read"],
}


def require_permission(permission: str):
    def dependency(user: dict = Depends(get_current_user)):
        role = user.get("role")

        if role not in permission_map:
            raise HTTPException(status_code=403, detail="Role not recognized")

        if permission not in permission_map[role]:
            raise HTTPException(status_code=403, detail="Permission denied")

        return user
    return dependency




#def require_permission(permission: str):
 #   def decorator(func):
  #      def wrapper(user=Depends(get_current_user), *args, **kwargs):
   #         role = user.get("role")
#
 #           if role not in permission_map:
  #              raise HTTPException(status_code=403, detail="Permission denied")
#
    #        if permission not in permission_map["role"]:
   #             raise HTTPException(status_code=403, detail="Permission denied")

     #       return func(*args, **kwargs)
      #  return wrapper
 #   return decorator




def permisson_required(permission: str):
    def checker(user: dict):
        role = user.get("role")

        if role not in permission_map:
            raise HTTPException(status_code=403, detail="Role not recognized")

        if permission not in permission_map[role]:
            raise HTTPException(status_code=403, detail="Permission denied")

    return checker




def admin_required(user: dict):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only Admin")
