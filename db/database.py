import sqlite3
import json
import hashlib
import os
from typing import Dict, Any, List, Optional
from models.problems import Submission, Problemset, Problem
from models.users import User, Classroom

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'judge.db')

def init_db(db_name: str = DEFAULT_DB_PATH):
    """
    Initialize the SQLite database and create the core tables.

    This function sets up the entire schema including Users, Problems, 
    Problemsets, and the various mapping tables for Classrooms.

    Parameters
    ----------
    db_name : str, optional
        The name of the database file. Defaults to 'judge.db'.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 1. USERS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. PROBLEMS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Problems (
            problem_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            time_limits TEXT NOT NULL,
            mem_limits TEXT NOT NULL,
            allowed_langs TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. PROBLEMSETS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Problemsets (
            problemset_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            set_type TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. PROBLEMSET_MAPPING TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Problemset_Mapping (
            problemset_id TEXT NOT NULL,
            problem_id TEXT NOT NULL,
            PRIMARY KEY (problemset_id, problem_id),
            FOREIGN KEY (problemset_id) REFERENCES Problemsets(problemset_id),
            FOREIGN KEY (problem_id) REFERENCES Problems(problem_id)
        )
    ''')

    # 5. SUBMISSIONS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Submissions (
            submission_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            problem_id TEXT NOT NULL,
            problemset_id TEXT,
            language TEXT NOT NULL,
            source_code TEXT NOT NULL,
            verdict TEXT DEFAULT 'Pending',
            execution_time REAL DEFAULT 0.0,
            passed_cases INTEGER DEFAULT 0,
            total_cases INTEGER DEFAULT 0,
            test_details TEXT,
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (problem_id) REFERENCES Problems(problem_id),
            FOREIGN KEY (problemset_id) REFERENCES Problemsets(problemset_id)
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_submission_user ON Submissions(user_id);
    ''')

    # 6. CLASSROOM TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Classroom (
            class_id TEXT PRIMARY KEY,
            teacher_id TEXT NOT NULL,
            class_name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 7. CLASSROOM - STUDENT MAPPING TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Class_Student_Mapping (
            class_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            PRIMARY KEY (class_id, student_id),
            FOREIGN KEY (class_id) REFERENCES Classroom(class_id),
            FOREIGN KEY (student_id) REFERENCES Users(user_id)
        )
    ''')

    # 8. CLASSROOM - PROBLEMSET MAPPING TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Class_Problemset_Mapping (
            class_id TEXT NOT NULL,
            problemset_id TEXT NOT NULL,
            PRIMARY KEY (class_id, problemset_id),
            FOREIGN KEY (class_id) REFERENCES Classroom(class_id),
            FOREIGN KEY (problemset_id) REFERENCES Problemsets(problemset_id)
        )
    ''')

    # ADD DEFAULT ADMIN
    default_pass = "12345678"
    admin_params = ('1', "admin", hashlib.sha256((default_pass + "admin").encode('utf-8')).hexdigest(), 'admin')
    cursor.execute(
        '''INSERT OR IGNORE INTO Users (user_id, username, password_hash, role) VALUES (?, ?, ?, ?)''', 
        admin_params
    )

    conn.commit()
    conn.close()

class DatabaseManager:
    """
    Handle all interactions with the SQLite database for the Online Judge system.
    
    Parameters
    ----------
    db_name : str, optional
        The path to the SQLite database file. Defaults to 'judge.db'.
    """

    def __init__(self, db_name: str = DEFAULT_DB_PATH):
        self.db_name = db_name

    def _execute_query(self, query: str, params: tuple = ()) -> None:
        """
        Helper method to execute a query and commit the transaction.

        Parameters
        ----------
        query : str
            The SQL query to execute.
        params : tuple, optional
            The parameters to bind to the query.
        """
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = 1")
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user from the database and hydrate it into a User object.

        Parameters
        ----------
        user_id : str
            The unique identifier of the user.

        Returns
        -------
        Optional[User]
            The hydrated Student, Teacher, or Admin object, or None if not found.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, password_hash, role FROM Users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row: return None
        uid, uname, pwd_hash, role = row
        if role == 'student':
            from models.users import Student
            return Student(user_id=uid, username=uname, password_hash=pwd_hash)
        elif role == 'teacher':
            from models.users import Teacher
            return Teacher(user_id=uid, username=uname, password_hash=pwd_hash)
        elif role == 'admin':
            from models.users import Admin
            return Admin(user_id=uid, username=uname, password_hash=pwd_hash)
        return User(user_id=uid, username=uname, password_hash=pwd_hash)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a user from the database using their unique username.

        Parameters
        ----------
        username : str
            The unique username to search for.

        Returns
        -------
        Optional[User]
            The hydrated user object, or None if not found.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, password_hash, role FROM Users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if not row: return None
        uid, uname, pwd_hash, role = row
        if role == 'student':
            from models.users import Student
            return Student(user_id=uid, username=uname, password_hash=pwd_hash)
        elif role == 'teacher':
            from models.users import Teacher
            return Teacher(user_id=uid, username=uname, password_hash=pwd_hash)
        elif role == 'admin':
            from models.users import Admin
            return Admin(user_id=uid, username=uname, password_hash=pwd_hash)
        return User(user_id=uid, username=uname, password_hash=pwd_hash)

    def save_user(self, user: User):
        """
        Save or update a user in the database.

        Parameters
        ----------
        user : User
            The user object to be stored.
        """
        role = user.__class__.__name__.lower()
        query = "INSERT OR REPLACE INTO Users (user_id, username, password_hash, role) VALUES (?, ?, ?, ?)"
        params = (user.user_id, user.username, user.password_hash, role)
        self._execute_query(query, params)

    def save_problem(self, problem: Problem):
        """
        Save or update a coding problem in the database.

        Parameters
        ----------
        problem : Problem
            The problem object containing metadata and constraints.
        """
        query = "INSERT OR REPLACE INTO Problems (problem_id, title, time_limits, mem_limits, allowed_langs) VALUES (?, ?, ?, ?, ?)"
        params = (
            problem.problem_id, 
            problem.title,
            json.dumps(problem.time_limits),
            json.dumps(problem.mem_limits),
            json.dumps(problem.allowed_langs)
        )
        self._execute_query(query, params)

    def save_submission(self, submission: Submission, result: Dict[str, Any], problemset_id: str = None):
        """
        Save the evaluation results of a code submission.

        Parameters
        ----------
        submission : Submission
            The submission object.
        result : Dict[str, Any]
            The detailed result dictionary from JudgeEngine.
        problemset_id : str, optional
            The ID of the problem set this submission belongs to.
        """
        details_json = json.dumps(result.get("details", []), ensure_ascii=False)
        query = '''
            INSERT OR REPLACE INTO Submissions 
            (submission_id, user_id, problem_id, problemset_id, language, source_code, 
             verdict, execution_time, passed_cases, total_cases, test_details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            submission.submission_id, submission.student_id, submission.problem_id,
            problemset_id, submission.language, submission.source_code,
            result.get("verdict", "System Error"), result.get("time_used", 0.0),
            result.get("passed_cases", 0), result.get("total_cases", 0), details_json
        )
        self._execute_query(query, params)

    def save_problemset(self, problemset: Problemset):
        """
        Save a problem set and its problem associations.

        Parameters
        ----------
        problemset : Problemset
            The problem set object to store.
        """
        query_ps = "INSERT OR REPLACE INTO Problemsets (problemset_id, title, set_type, start_time, end_time) VALUES (?, ?, ?, ?, ?)"
        params_ps = (
            problemset.problemset_id, problemset.title, problemset.set_type,
            problemset.start_time.isoformat(), problemset.end_time.isoformat()
        )
        self._execute_query(query_ps, params_ps)

        self._execute_query("DELETE FROM Problemset_Mapping WHERE problemset_id = ?", (problemset.problemset_id,))
        query_mapping = "INSERT INTO Problemset_Mapping (problemset_id, problem_id) VALUES (?, ?)"
        for prob_id in problemset.problem_ids:
            self._execute_query(query_mapping, (problemset.problemset_id, prob_id))

    def save_classroom(self, classroom: Classroom):
        """
        Save a classroom and synchronize its students and problem sets.

        Parameters
        ----------
        classroom : Classroom
            The classroom object to synchronize.
        """
        query = "INSERT OR REPLACE INTO Classroom (class_id, teacher_id, class_name) VALUES (?, ?, ?)"
        params = (classroom.class_id, classroom.teacher_id, classroom.class_name)
        self._execute_query(query, params)
        
        self._execute_query("DELETE FROM Class_Student_Mapping WHERE class_id = ?", (classroom.class_id,))
        for student_id in classroom.student_ids:
            self._execute_query("INSERT INTO Class_Student_Mapping (class_id, student_id) VALUES (?, ?)", (classroom.class_id, student_id))
            
        self._execute_query("DELETE FROM Class_Problemset_Mapping WHERE class_id = ?", (classroom.class_id,))
        for ps_id in classroom.problemset_ids:
            self._execute_query("INSERT INTO Class_Problemset_Mapping (class_id, problemset_id) VALUES (?, ?)", (classroom.class_id, ps_id))

    def get_classroom(self, class_id: str) -> Optional[Classroom]:
        """
        Retrieve a classroom from the database and hydrate its relationships.

        Parameters
        ----------
        class_id : str
            The ID of the classroom to retrieve.

        Returns
        -------
        Optional[Classroom]
            The hydrated Classroom object with student and problem set IDs, or None.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT class_id, teacher_id, class_name FROM Classroom WHERE class_id = ?", (class_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        cls = Classroom(class_id=row[0], teacher_id=row[1], class_name=row[2])
        
        cursor.execute("SELECT student_id FROM Class_Student_Mapping WHERE class_id = ?", (class_id,))
        for s_row in cursor.fetchall(): cls.add_student(s_row[0])
            
        cursor.execute("SELECT problemset_id FROM Class_Problemset_Mapping WHERE class_id = ?", (class_id,))
        for p_row in cursor.fetchall(): cls.assign_problemset(p_row[0])
            
        conn.close()
        return cls
    
    def get_problem(self, problem_id: str) -> Problem:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT problem_id, title, time_limits, mem_limits, allowed_langs FROM Problems WHERE problem_id = ?", (problem_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None
            
        return Problem(
            problem_id=row[0],
            title=row[1],
            description="Loaded from DB",
            time_limits=json.loads(row[2]),
            mem_limits=json.loads(row[3]),
            allowed_lang=json.loads(row[4])
        )

    def get_problemset(self, problemset_id: str) -> Problem:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT problemset_id, title, set_type, start_time, end_time FROM Problemsets WHERE problemset_id = ?", (problemset_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None
            
        return Problemset(
            problemset_id=row[0],
            title=row[1],
            start_time=row[3],
            end_time=row[4],
            set_type=row[2]
        )
    
    def get_problemset_scores(self, problemset_id: str) -> list:
        """
        Fetch the highest score per user for a specific problem set.
        Returns a list of tuples containing (user_id, total_score).
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        query = '''
            SELECT user_id, SUM(max_passed) as total_score
            FROM (
                SELECT user_id, problem_id, MAX(passed_cases) as max_passed
                FROM Submissions
                WHERE problemset_id = ?
                GROUP BY user_id, problem_id
            )
            GROUP BY user_id
        '''
        
        cursor.execute(query, (problemset_id,))
        results = cursor.fetchall()
        conn.close()
        
        return results

if __name__ == "__main__":
    init_db()