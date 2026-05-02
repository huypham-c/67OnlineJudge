from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import datetime
import asyncio
import time
import os
import shutil
import zipfile
import json
import tempfile
import sqlite3
from typing import Optional, List, Dict
from pydantic import BaseModel
from contextlib import asynccontextmanager

from db.database import DatabaseManager
from models.users import User
from core.judge import JudgeEngine
from core.libs import PriorityQueue, BST

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the lifecycle of the FastAPI application.

    Starts the background worker for judging submissions upon startup 
    and gracefully cancels it during shutdown.

    Parameters
    ----------
    app : FastAPI
        The FastAPI application instance.
    """
    worker_task = asyncio.create_task(background_judge_worker())
    print("Background worker activated!")
    
    yield
    
    print("Stopping server")
    worker_task.cancel()

app = FastAPI(title="67 Online Judge", lifespan=lifespan)

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

class TestCaseManual(BaseModel):
    input: str
    output: str
    hidden: bool

class ProblemManualRequest(BaseModel):
    title: str
    description: str
    allowed_langs: List[str]
    time_limits: Dict[str, float]
    mem_limits: Dict[str, int]
    test_cases: List[TestCaseManual]

class AssignProblemsRequest(BaseModel):
    problem_ids: List[str]

class CreateClassroomRequest(BaseModel):
    class_name: str
    student_ids: List[str] = []

class CreateProblemsetRequest(BaseModel):
    title: str
    description: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    problem_ids: List[str] = []

class UpdateUserRoleRequest(BaseModel):
    user_id: str
    new_role: str

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
    """
    Process code submissions continuously in the background.

    Pops pending submissions from the priority queue and evaluates them 
    asynchronously using the judge engine, then saves the result.
    """
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


@app.post("/problems/create/manual")
async def create_problem_manual(
    request: ProblemManualRequest,
    user_id: str = Depends(get_current_user_id)
) -> dict:
    """
    Create a new problem manually using raw data.

    Parameters
    ----------
    request : ProblemManualRequest
        The payload containing problem constraints, description, and test cases.
    user_id : str
        The ID of the authenticated user attempting to create the problem.

    Returns
    -------
    dict
        A dictionary containing the creation status and the new problem ID.

    Raises
    ------
    HTTPException
        If the authenticated user lacks teacher or admin privileges.
    """
    user = db.get_user(user_id)
    if user.__class__.__name__.lower() == 'student':
        raise HTTPException(status_code=403, detail="Only teachers can create problems")

    problem = user.create_problem(
        title=request.title,
        description="Stored in file",
        time_limits=request.time_limits,
        mem_limits=request.mem_limits,
        allowed_langs=request.allowed_langs
    )

    formatted_tc = [(tc.input, tc.output) for tc in request.test_cases]
    banned_words = ["os.system", "subprocess", "eval", "exec"]
    
    problem.save_problem_data(
        html_content=request.description,
        testcases=formatted_tc,
        banned_words=banned_words
    )
    
    db.save_problem(problem)
    return {"status": "success", "message": "Problem created successfully", "problem_id": problem.problem_id}


@app.post("/problems/create/zip")
async def create_problem_zip(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
) -> dict:
    """
    Import a problem directly from a compressed ZIP archive.

    Extracts metadata and test cases from the ZIP file to construct 
    and save the problem structure automatically.

    Parameters
    ----------
    file : UploadFile
        The uploaded ZIP file containing problem data.
    user_id : str
        The ID of the authenticated user performing the import.

    Returns
    -------
    dict
        A status payload indicating successful import alongside the problem ID.
    """
    user = db.get_user(user_id)
    if user.__class__.__name__.lower() == 'student':
        raise HTTPException(status_code=403, detail="Only teachers can create problems")
        
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a ZIP file.")

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        extract_dir = os.path.join(temp_dir, "extracted")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        metadata_path = os.path.join(extract_dir, "metadata.json")
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=400, detail="metadata.json not found inside the ZIP file")
            
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        problem = user.create_problem(
            title=metadata.get("title", "Imported Problem"),
            description="Stored in file",
            time_limits=metadata.get("time_limits", {"python": 2.0, "cpp": 1.0}),
            mem_limits=metadata.get("mem_limits", {"python": 512, "cpp": 256}),
            allowed_langs=metadata.get("allowed_langs", ["python", "cpp"])
        )

        problem.folder_path = os.path.join("data", "problems", problem.problem_id)
        os.makedirs(problem.folder_path, exist_ok=True)
        
        for item in os.listdir(extract_dir):
            if item != "metadata.json":
                s = os.path.join(extract_dir, item)
                d = os.path.join(problem.folder_path, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
                    
        db.save_problem(problem)
        
    finally:
        shutil.rmtree(temp_dir)
        
    return {"status": "success", "message": "ZIP Problem imported successfully", "problem_id": problem.problem_id}


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

    banned_words = problem.get_banned_words()
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
    Retrieve the current leaderboard for a specific problem set.

    Utilizes the custom Red-Black Tree (BST) to efficiently sort and 
    balance the highest scores of the participants.

    Parameters
    ----------
    problemset_id : str
        The unique identifier of the problem set.

    Returns
    -------
    dict
        A structured response containing the ranked user list and scores.
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

@app.get("/users/me/classrooms")
async def get_my_classrooms(user_id: str = Depends(get_current_user_id)) -> dict:
    classes = db.get_user_classrooms(user_id)
    return {"classrooms": classes}

@app.get("/classrooms/{class_id}/problemsets")
async def get_classroom_problemsets(class_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    sets = db.get_classroom_problemsets(class_id)
    return {"problemsets": sets}

@app.get("/problemsets/{problemset_id}/problems")
async def get_problemset_problems(problemset_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    probs = db.get_problemset_problems(problemset_id)
    return {"problems": probs}

@app.get("/problems/{problem_id}")
async def get_problem_details(problem_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    problem = db.get_problem(problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    description_html = problem.description
    desc_path = os.path.join(problem.folder_path, "description.html")
    if os.path.exists(desc_path):
        with open(desc_path, "r", encoding="utf-8") as f:
            description_html = f.read()

    return {
        "problem_id": problem.problem_id,
        "title": problem.title,
        "description": description_html,
        "time_limits": problem.time_limits,
        "mem_limits": problem.mem_limits,
        "allowed_langs": problem.allowed_langs
    }

@app.get("/submissions/{submission_id}")
async def check_submission_status(submission_id: str) -> dict:
    sub_data = db.get_submission(submission_id)
    if not sub_data:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return sub_data


@app.get("/problems")
async def get_all_problems(user_id: str = Depends(get_current_user_id)):
    """
    Fetch a summarized list of all available problems in the system.

    This endpoint is strictly restricted to teachers and administrators 
    for problem assignment operations.

    Parameters
    ----------
    user_id : str
        The authenticated user's ID injected by the dependency.

    Returns
    -------
    dict
        A structured list mapping problem IDs to their respective titles.
    """
    user = db.get_user(user_id)
    if user.__class__.__name__.lower() not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT problem_id, title FROM Problems ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return {"problems": [{"problem_id": r[0], "title": r[1]} for r in rows]}

@app.post("/problemsets/{problemset_id}/assign")
async def assign_problems_to_set(
    problemset_id: str, 
    request: AssignProblemsRequest, 
    user_id: str = Depends(get_current_user_id)
):
    """
    Safely append a batch of problems to an existing problem set.

    Parameters
    ----------
    problemset_id : str
        The ID of the target problem set.
    request : AssignProblemsRequest
        A JSON payload containing the list of problem IDs to append.
    user_id : str
        The ID of the authenticated user initiating the assignment.

    Returns
    -------
    dict
        A confirmation dictionary indicating the number of appended problems.
    """
    user = db.get_user(user_id)
    if user.__class__.__name__.lower() not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    problemset = db.get_problemset(problemset_id)
    if not problemset:
        raise HTTPException(status_code=404, detail="Problemset not found")
        
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT problem_id FROM Problemset_Mapping WHERE problemset_id = ?", (problemset_id,))
    existing_ids = [r[0] for r in cursor.fetchall()]
    conn.close()
    
    for pid in existing_ids:
        problemset.add_problem(pid)
    for pid in request.problem_ids:
        problemset.add_problem(pid)
        
    db.save_problemset(problemset)
    return {"status": "success", "message": f"Assigned {len(request.problem_ids)} problems to set"}

@app.post("/classrooms")
async def create_classroom(
    request: CreateClassroomRequest,
    user_id: str = Depends(get_current_user_id)
) -> dict:
    """
    Create a new classroom.

    This endpoint is restricted to teachers and administrators. It initializes
    a new classroom and optionally enrolls a list of student IDs.

    Parameters
    ----------
    request : CreateClassroomRequest
        The payload containing the classroom name and an optional list of student IDs.
    user_id : str
        The ID of the authenticated user creating the classroom.

    Returns
    -------
    dict
        A status dictionary containing the success message and the new classroom ID.

    Raises
    ------
    HTTPException
        If the authenticated user lacks teacher or admin privileges.
    """
    user = db.get_user(user_id)
    if user.__class__.__name__.lower() not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    classroom = user.create_classroom(request.class_name)
    for student_id in request.student_ids:
        classroom.add_student(student_id)
        
    db.save_classroom(classroom)
    return {"status": "success", "message": "Classroom created", "class_id": classroom.class_id}

@app.post("/problemsets")
async def create_problemset(
    request: CreateProblemsetRequest,
    user_id: str = Depends(get_current_user_id)
) -> dict:
    """
    Create a new problem set or contest.

    This endpoint allows teachers and administrators to group problems into
    a specific set with defined start and end times.

    Parameters
    ----------
    request : CreateProblemsetRequest
        The payload containing the title, description, time bounds, and problem IDs.
    user_id : str
        The ID of the authenticated user creating the problem set.

    Returns
    -------
    dict
        A status dictionary containing the success message and the new problemset ID.

    Raises
    ------
    HTTPException
        If the authenticated user lacks teacher or admin privileges.
    """
    user = db.get_user(user_id)
    if user.__class__.__name__.lower() not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    problemset = user.create_problem_set(
        title=request.title,
        description=request.description,
        problemset=request.problem_ids,
        start_time=request.start_time,
        end_time=request.end_time
    )
    
    db.save_problemset(problemset)
    return {"status": "success", "message": "Problem set created", "problemset_id": problemset.problemset_id}

@app.get("/users")
async def get_all_users(user_id: str = Depends(get_current_user_id)) -> dict:
    """
    Retrieve a list of all registered users in the system.

    This endpoint is strictly restricted to administrators for system management
    and role assignment purposes.

    Parameters
    ----------
    user_id : str
        The ID of the authenticated user requesting the list.

    Returns
    -------
    dict
        A dictionary containing a list of user details including ID, username, and role.

    Raises
    ------
    HTTPException
        If the authenticated user is not an administrator.
    """
    user = db.get_user(user_id)
    if user.__class__.__name__.lower() != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
        
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, role FROM Users ORDER BY username")
    rows = cursor.fetchall()
    conn.close()
    
    return {"users": [{"user_id": r[0], "username": r[1], "role": r[2]} for r in rows]}

@app.post("/users/role")
async def update_user_role(
    request: UpdateUserRoleRequest,
    user_id: str = Depends(get_current_user_id)
) -> dict:
    """
    Update the system role of a specific user.

    This endpoint allows administrators to promote or demote users between
    student, teacher, and admin roles.

    Parameters
    ----------
    request : UpdateUserRoleRequest
        The payload specifying the target user ID and their new role.
    user_id : str
        The ID of the authenticated administrator making the change.

    Returns
    -------
    dict
        A status dictionary confirming the role update.

    Raises
    ------
    HTTPException
        If the authenticated user is not an administrator, if the specified role
        is invalid, or if the target user is not found.
    """
    admin = db.get_user(user_id)
    if admin.__class__.__name__.lower() != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
        
    if request.new_role not in ['student', 'teacher', 'admin']:
        raise HTTPException(status_code=400, detail="Invalid role specified")
        
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    cursor.execute("UPDATE Users SET role = ? WHERE user_id = ?", (request.new_role, request.user_id))
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    conn.close()
    return {"status": "success", "message": f"User role updated to {request.new_role}"}