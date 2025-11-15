from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from .db import users_collection
from .schemas import UserPublic, UserUpdate, ChangePassword
from .security import decode_access_token, hash_password, verify_password

user_router = APIRouter()
oauth2_scheme = HTTPBearer()


# -------- Helper: Extract user from token ----------
async def get_current_user(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    jwt_token = token.credentials   # <-- THIS extracts the real token string

    payload = decode_access_token(jwt_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert ObjectId to string for response
    user["id"] = str(user["_id"])
    return user


# -------- GET /users/me ----------
@user_router.get("/me", response_model=UserPublic)
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user.get("name")
    }


# -------- PUT /users/me ----------
@user_router.put("/me", response_model=UserPublic)
async def update_profile(
    data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    update_data = {k: v for k, v in data.dict().items() if v is not None}

    await users_collection.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": update_data}
    )

    updated = await users_collection.find_one({"_id": ObjectId(current_user["id"])})

    return {
        "id": str(updated["_id"]),
        "email": updated["email"],
        "name": updated.get("name") or updated.get("username")
    }


# -------- PUT /users/me/password ----------
@user_router.put("/me/password")
async def change_password(
    data: ChangePassword,
    current_user: dict = Depends(get_current_user)
):

    stored_password = current_user.get("password") or current_user.get("password_hash")

    if not stored_password:
        raise HTTPException(status_code=500, detail="Password field missing in DB")

    if not verify_password(data.old_password, stored_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    new_hash = hash_password(data.new_password)

    await users_collection.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": {"password": new_hash}}
    )

    return {"message": "Password changed successfully"}
