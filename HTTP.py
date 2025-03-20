from fastapi import FastAPI, HTTPException, Path, Body, Depends, Request
from pydantic import BaseModel, Field
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from typing import Optional
import base64

app = FastAPI()

# 仮のデータベース
fake_db = {}

# ユーザー登録リクエストモデル
class UserSignup(BaseModel):
    user_id: str = Field(..., min_length=6, max_length=20, pattern="^[a-zA-Z0-9]+$")
    password: str = Field(..., min_length=8, max_length=20, pattern="^[a-zA-Z0-9!@#$%^&*()_+=-]+$")

# ユーザー更新リクエストモデル
class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(None, max_length=30)
    comment: Optional[str] = Field(None, max_length=100)

# アカウント削除リクエストモデル
class AccountDelete(BaseModel):
    confirm: bool

# 認証処理
def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        raise HTTPException(status_code=401, detail={"message": "Authentication failed"})

    try:
        encoded_credentials = auth_header.split(" ")[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
        user_id, password = decoded_credentials.split(":", 1)
    except Exception:
        raise HTTPException(status_code=401, detail={"message": "Authentication failed"})

    user = fake_db.get(user_id)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail={"message": "Authentication failed"})

    return user_id

# ユーザー登録
@app.post("/signup")
def signup(user: UserSignup):
    if user.user_id in fake_db:
        raise HTTPException(status_code=400, detail={"message": "Account creation failed", "cause": "Already same user_id is used"})

    fake_db[user.user_id] = {"user_id": user.user_id, "password": user.password, "nickname": user.user_id, "comment": ""}
    
    return {
        "message": "Account successfully created",
        "user": {"user_id": user.user_id, "nickname": user.user_id}
    }

# ユーザー情報取得
@app.get("/users/{user_id}")
def get_user(user_id: str = Path(..., min_length=6, max_length=20), current_user: str = Depends(get_current_user)):
    user = fake_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "No user found"})
    


    return {
        "message": "User details by user_id",
        "user": {
            "user_id": user["user_id"],
            "nickname": user["nickname"],
            "comment": user["comment"]
        }
    }

# ユーザー情報更新
@app.patch("/users/{user_id}")
def update_user(user_id: str, update_data: UserUpdate, current_user: str = Depends(get_current_user)):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail={"message": "No permission for update"})

    user = fake_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "No user found"})

    if update_data.nickname is not None:
        user["nickname"] = update_data.nickname if update_data.nickname else user_id
    if update_data.comment is not None:
        user["comment"] = update_data.comment if update_data.comment else ""

    return {
        "message": "User successfully updated",
        "user": {
            "nickname": user["nickname"],
            "comment": user["comment"]
        }
    }

# アカウント削除
@app.post("/close")
def close_account(data: AccountDelete = Body(...), current_user: str = Depends(get_current_user)):
    if current_user in fake_db:
        del fake_db[current_user]
        return {"message": "Account and user successfully removed"}
    
    raise HTTPException(status_code=401, detail={"message": "Authentication failed"})
