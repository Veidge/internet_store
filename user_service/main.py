from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uuid
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()

# Модель пользователя
class User(BaseModel):
    id: str
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    disabled: Optional[bool] = False

class UserCreate(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    disabled: Optional[bool] = None

# Временное in-memory хранилище
users_db = {}

# Регистрация пользователя
@app.post("/users/", response_model=User)
def register_user(user: UserCreate):
    user_id = str(uuid.uuid4())
    new_user = User(id=user_id, **user.dict())
    users_db[user_id] = new_user
    return new_user

# Получить всех пользователей
@app.get("/users/", response_model=List[User])
def get_users():
    return list(users_db.values())

# Получить пользователя по ID
@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: str):
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Обновить пользователя
@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: str, user_update: UserUpdate):
    stored_user = users_db.get(user_id)
    if not stored_user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_data = user_update.dict(exclude_unset=True)
    updated_user = stored_user.copy(update=updated_data)
    users_db[user_id] = updated_user
    return updated_user

# Удалить пользователя
@app.delete("/users/{user_id}")
def delete_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    del users_db[user_id]
    return {"message": "User deleted"}
