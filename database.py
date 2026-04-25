import sqlite3
import json

def init_db(db_name: str = "judge.db"):
    """
    Initialize the SQLite database and create the core tables, 
    including Problemsets for contests and assignments.

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

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()