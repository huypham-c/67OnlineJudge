from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import datetime
from typing import Optional
from pydantic import BaseModel

from database import DatabaseManager
from users import User
from judge import JudgeEngine

app = FastAPI(title="67")

SECRET_KEY = "something"
ALGORITHM = "HS256"

security = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Extract and validate the JWT token to authenticate the user.

    Parameters
    ----------
    credentials : HTTPAuthorizationCredentials
        The bearer token provided in the authorization header.

    Returns
    -------
    str
        The extracted user_id from the valid token.

    Raises
    ------
    HTTPException
        If the token is missing, expired, or invalid.
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
    """
    Pydantic model representing the expected body for login requests.
    
    Parameters
    ----------
    username : str
        The user's login name.
    password : str
        The user's plain text password.
    """
    username: str
    password: str
    
class SubmitCodeRequest(BaseModel):
    """
    Pydantic model representing the expected body for submission request.
    
    Parameters
    ----------
    source_code : str
        The source code to submit.
    language : str
        The language the source code is in.
    problemset_id : str
        The id of the problemset the submission is for.
    """
    source_code: str
    language: str
    problemset_id: str

def create_access_token(data: dict) -> str:
    """
    Generate a stateless JWT access token for a given user payload.

    Parameters
    ----------
    data : dict
        The payload data to encode into the token (e.g., user_id, role).

    Returns
    -------
    str
        The encoded JWT string valid for 24 hours.
    """
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@app.post("/login")
async def login(request: LoginRequest) -> dict:
    """
    Authenticate a user and issue a JWT token.

    Parameters
    ----------
    request : LoginRequest
        The JSON body containing username and password.

    Returns
    -------
    dict
        A dictionary containing the access_token, token_type, username, and role.
        
    Raises
    ------
    HTTPException
        If the user is not found or the password is incorrect.
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


@app.get("/me")
async def get_my_profile(user_id: str = Depends(get_current_user_id)) -> dict:
    """
    Retrieve the basic profile information of the currently authenticated user.

    Parameters
    ----------
    user_id : str
        The ID of the user, automatically injected by the token dependency.

    Returns
    -------
    dict
        A success message including the authenticated user's ID.
    """
    return {
        "status": "success",
        "message": "Token validation successful!",
        "your_user_id_is": user_id
    }
@app.post("/problems/{problem_id}/submit")
async def submit_code(
    problem_id: str,
    request: SubmitCodeRequest,
    user_id: str = Depends(get_current_user_id)
) -> dict:
    
    if not request.problemset_id or not request.problemset_id.strip():
        raise HTTPException(
            status_code=400, 
            detail="A valid problemset_id is strictly required to submit code."
        )

    user = db.get_user(user_id)
    problem = db.get_problem(problem_id)
    
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    if request.language not in problem.allowed_langs:
        raise HTTPException(status_code=400, detail=f"{request.language} is not allowed")

    banned_words = ["os.system", "subprocess", "eval", "exec", "open", "__import__"]
    for word in banned_words:
        if word in request.source_code:
            raise HTTPException(
                status_code=403, 
                detail=f"Found banned keyword: {word} in the submission"
            )

    submission = user.submit_code(
        problem_id=problem.problem_id,
        source_code=request.source_code,
        language=request.language
    )

    judge = JudgeEngine()
    result = judge.evaluate_submission(submission, problem)

    db.save_submission(submission, result, request.problemset_id)

    return {
        "status": "success",
        "submission_id": submission.submission_id,
        "verdict": result["verdict"],
        "execution_time": result["time_used"],
        "passed_cases": result["passed_cases"],
        "total_cases": result.get("total_cases", 0),
        "details": result.get("details", [])
    }