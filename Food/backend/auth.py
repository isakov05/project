# Food/backend/auth.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from bson import ObjectId

from .db import users_collection
from .security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

auth_router = APIRouter()
bearer = HTTPBearer()


# -----------------------------
# Pydantic Models
# -----------------------------
class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


# -----------------------------
# SIGNUP
# -----------------------------
@auth_router.post("/signup")
async def signup(user: UserRegister):

    # email exists?
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(400, detail="Email already registered")

    # username exists?
    if await users_collection.find_one({"username": user.username}):
        raise HTTPException(400, detail="Username already taken")

    hashed = hash_password(user.password)

    new_user = {
        "username": user.username,
        "email": user.email,
        "password": hashed,
    }

    await users_collection.insert_one(new_user)

    return {"message": "User registered successfully!"}


# -----------------------------
# LOGIN
# -----------------------------
@auth_router.post("/login")
async def login(user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})

    if not db_user:
        raise HTTPException(400, detail="Invalid email or password")

    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(400, detail="Invalid email or password")

    # create token
    access_token = create_access_token({"user_id": str(db_user["_id"])})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": db_user["username"]
    }


# -----------------------------
# AUTH GUARD
# -----------------------------
async def require_user(token: HTTPAuthorizationCredentials = Depends(bearer)):
    """Extract user from Authorization: Bearer <token>"""
    payload = decode_access_token(token.credentials)

    if payload is None:
        raise HTTPException(401, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(401, detail="Token missing user_id")

    # verify user exists
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(404, detail="User not found")

    return payload  # gives access to user_id in other routes
