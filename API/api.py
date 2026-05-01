from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import datetime
import asyncio
import time
from typing import Optional
from pydantic import BaseModel
from contextlib import asynccontextmanager

from db.database import DatabaseManager
from models.users import User
from core.judge import JudgeEngine
from core.libs import PriorityQueue, BST

@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = asyncio.create_task(background_judge_worker())
    print("Background worker activated!")
    
    yield
    
    print("Stopping server")
    worker_task.cancel()

app = FastAPI(title="67", lifespan=lifespan)

SECRET_KEY = "something"
ALGORITHM = "HS256"

security = HTTPBearer()
db = DatabaseManager()

submission_queue = PriorityQueue()
judge = JudgeEngine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    username: str
    password: str
    
class SubmitCodeRequest(BaseModel):
    source_code: str
    language: str
    problemset_id: str


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


async def background_judge_worker():

    loop = asyncio.get_running_loop()
    
    while True:
        if len(submission_queue) > 0:
            priority, submission, problem, problemset_id = submission_queue.pop()
            
            result = await loop.run_in_executor(
                None, 
                judge.evaluate_submission, 
                submission, 
                problem
            )
            
            db.save_submission(submission, result, problemset_id)
        else:
            await asyncio.sleep(2)


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
            raise HTTPException(status_code=403, detail=f"Found banned keyword: {word} in the submission")

    submission = user.submit_code(
        problem_id=problem.problem_id,
        source_code=request.source_code,
        language=request.language
    )

    db.save_submission(submission, {"verdict": "Pending", "time_used": 0.0}, request.problemset_id)

    problemset = db.get_problemset(request.problemset_id)
    set_type = problemset.set_type
    priority_score = time.time() * -1 + 100 if set_type == "contest" else 0
    submission_queue.insert((priority_score, submission, problem, request.problemset_id))

    return {
        "status": "success",
        "message": "Submission received and queued for grading.",
        "submission_id": submission.submission_id
    }


@app.get("/problemsets/{problemset_id}/leaderboard")
async def get_leaderboard(problemset_id: str) -> dict:
    """
    Extract scores from database and utilize the custom Red-Black Tree 
    to generate a perfectly balanced descending leaderboard.
    """
    raw_scores = db.get_problemset_scores(problemset_id)
    def comparator(a: tuple, b: tuple) -> bool:
        if a[0] == b[0]:
            return a[1] > b[1] 
        return a[0] < b[0]
    
    leaderboard_tree = BST(comparator=comparator)
    
    for user_id, score in raw_scores:
        leaderboard_tree.insert((score, user_id))
        
    sorted_elements = leaderboard_tree.get_sorted_elements()
    
    response_data = []
    for rank, (score, uid) in enumerate(sorted_elements, start=1):
        user_info = db.get_user(uid)
        username = user_info.username if user_info else "Unknown User"
        
        response_data.append({
            "rank": rank,
            "username": username,
            "score": score
        })
        
    return {
        "problemset_id": problemset_id,
        "leaderboard": response_data
    }