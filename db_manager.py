import sqlite3
import json
from typing import Dict, Any
from problems import Submission
from users import User
from problems import Problemset, Problem

class DatabaseManager:
    """
    Handle all interactions with the SQLite database for the Judge system.
    
    Parameters
    ----------
    db_name : str, optional
        The path to the SQLite database file. Defaults to 'judge.db'.
    """

    def __init__(self, db_name: str = "judge.db"):
        self.db_name = db_name

    def _execute_query(self, query: str, params: tuple = ()) -> None:
        """Helper method to execute a query and commit the transaction."""
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = 1")
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
        except sqlite3.IntegrityError:
            # Ignore errors like duplicate inserts for mock data setup
            pass
        finally:
            conn.close()

    def save_user(self, user: 'User'):
        """
        Save the a new user to the database.

        Parameters
        ----------
        user : User
            The user object containing metadata of the user.
        role : str
            The string define the privilege level of the user in the system.
        """
        role = user.__class__.__name__.lower()
        query = "INSERT OR REPLACE INTO Users (user_id, username, password_hash, role) VALUES (?, ?, ?, ?)"
        params = (user.user_id, user.username, user.password_hash, role)
        self._execute_query(query, params)

    def save_problem(self, problem: 'Problem'):
        """
        Save the a problem and its metadata to the database.

        Parameters
        ----------
        problem : Problem
            The problem object containing metadata.
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

    def save_submission(self, submission: 'Submission', result: Dict[str, Any], problemset_id: str = None) -> None:
        """
        Save the evaluated submission and its detailed results to the database.

        Parameters
        ----------
        submission : Submission
            The submission object containing metadata and source code.
        result : Dict[str, Any]
            The evaluation dictionary returned by JudgeEngine.
        problemset_id : str, optional
            The ID of the contest or assignment, if applicable.
        """
        details_json = json.dumps(result.get("details", []), ensure_ascii=False)
        
        query = '''
            INSERT OR REPLACE INTO Submissions 
            (submission_id, user_id, problem_id, problemset_id, language, source_code, 
             verdict, execution_time, passed_cases, total_cases, test_details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        params = (
            submission.submission_id,
            submission.student_id,
            submission.problem_id,
            problemset_id,
            submission.language,
            submission.source_code,
            result.get("verdict", "System Error"),
            result.get("time_used", 0.0),
            result.get("passed_cases", 0),
            result.get("total_cases", 0),
            details_json
        )
        
        self._execute_query(query, params)

    def save_problemset(self, problemset: 'Problemset'):
        """
        Save a new problemset and its associated problems to the database.

        Parameters
        ----------
        problemset : Problemset
            The problemset object containing timing metadata and a set of problem IDs.
        """
        set_type = problemset.__class__.__name__.lower()
        
        query_ps = '''
            INSERT OR REPLACE INTO Problemsets (problemset_id, title, set_type, start_time, end_time) 
            VALUES (?, ?, ?, ?, ?)
        '''

        
        params_ps = (
            problemset.problemset_id,
            problemset.title,
            set_type,
            problemset.start_time.isoformat(),
            problemset.end_time.isoformat()
        )
        self._execute_query(query_ps, params_ps)

        self._execute_query("DELETE FROM Problemset_Mapping WHERE problemset_id = ?", (problemset.problemset_id,))

        query_mapping = "INSERT INTO Problemset_Mapping (problemset_id, problem_id) VALUES (?, ?)"
        for prob_id in problemset.problem_ids:
            self._execute_query(query_mapping, (problemset.problemset_id, prob_id))