from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import datetime
from typing import Optional
from pydantic import BaseModel

from database import DatabaseManager
from users import User

app = FastAPI(title="67")

SECRET_KEY = "something"
ALGORITHM = "HS256"

security = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Hàm gác cổng: Bóc tách Token do người dùng gửi lên để lấy ra user_id.
    Nếu Token giả hoặc hết hạn, tự động đuổi ra ngoài (Lỗi 401).
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Expired token, please login again")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Can not validate token")

db = DatabaseManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    username: str
    password: str

def create_access_token(data: dict):
    """Generate a stateless JWT token for the user."""
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.get("/")
async def root():
    """Trang chủ của API"""
    return {"message": "Chào mừng đến với Hệ thống Online Judge!"}

@app.post("/login")
async def login(request: LoginRequest):
    """
    Endpoint to authenticate users and issue a JWT token.
    The frontend will send username/password, and we return a 'passport'.
    """
    user = db.get_user_by_username(request.username)
    
    if not user:
        raise HTTPException(status_code=404, detail="Username not found")
    
    if not user.verify_password(request.password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    token = create_access_token(data={"user_id": user.user_id, "role": user.__class__.__name__.lower()})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.__class__.__name__.lower()
    }

@app.get("/health")
async def health_check():
    """Simple endpoint to verify if the server is running."""
    return {"status": "online", "server_location": "Vung Tau"}

@app.get("/me")
async def get_my_profile(user_id: str = Depends(get_current_user_id)):
    """
    Endpoint yêu cầu phải có Token mới xem được.
    Trả về thông tin của chính người đang đăng nhập.
    """
    
    return {
        "status": "success",
        "message": "Bạn đã vượt qua trạm kiểm soát thành công!",
        "your_user_id_is": user_id
    }
