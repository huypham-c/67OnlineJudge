import datetime

class User:
    """Base class for a user in the judge system."""

    def __init__(self, user_id: str, username: str, password_hash: str):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
    
    def login(self):
        """Login and verify user logic."""
        pass
    
    def view_leaderboard(self):
        """Let user view leaderboard of a contest."""
        pass

class Student(User):
    """Class for a user with student access in the system, inherited from User."""

    def __init__(self, user_id: str, username: str, password_hash: str):
        super().__init__(user_id, username, password_hash)
        self.class_ids = set()

    def enroll(self, class_id: str):
        """Add the student to a new classroom."""
        self.class_ids.add(class_id)

    def submit_code(self, problem_id: str, source_code: str, language: str):
        """Method for submitting a solution to a specific problem."""
        pass

class Teacher(User):
    """Class for a user with teacher access in the system, inherited from User."""

    def create_problem(self, title: str, description: str, time_limit: float, mem_limit: int):
        """Method to create a new problem in the system."""
        pass

    def create_problem_set(self, title: str, description: str, problemset: list, start_time: datetime.datetime, end_time: datetime.datetime):
        """Method let teacher create a new contest or assignment."""
        pass

    def manage_test_cases(self, problem_id: str):
        """Method to create, modify or delete test cases."""
        pass

    def view_completions(self):
        """Let teacher view who complete assignments."""
        pass

class Admin(Teacher):
    """Class for a user with Admin access in the system, inherited from Teacher."""

    def create_user_account(self, role: str, username: str):
        """Method to create new accounts."""
        pass