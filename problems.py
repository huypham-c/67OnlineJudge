import datetime

class Problem:
    """Represent for a problem in the system."""
    
    class TestCase:
        """Represent a test case in a problem."""

        def __init__(self, test_id: str, input_data: str, expected_output: str, is_hidden: bool = False):
            self.test_id = test_id
            self.input_data = input_data
            self.expected_output = expected_output
            self.is_hidden = is_hidden

    def __init__(self, problem_id: str, title: str, description: str, time_limit: float = 1.0, mem_limit: int = 256):
        self.problem_id = problem_id
        self.title = title
        self.description = description
        self.time_limit = time_limit
        self.mem_limit = mem_limit
        self.test_cases = []

    def add_test_cases(self, test_case: TestCase):
        """Add a new test case to the problem."""
        pass

    def get_public_test(self):
        """Get public test cases to add as example for the problem."""
        pass

class Problemset:
    """Base class represent a collection of problems."""
    def __init__(self, problemset_id: str, title: str, start_time: datetime.datetime, end_time: datetime.datetime):
        self.problemset_id = problemset_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.problem_ids = set()

    def add_problem(self, problem: Problem):
        """Add problem to the problemset."""
        pass

class Contest(Problemset):
    """Represent a contest (with public leaderboard)."""
    pass

class Assignment(Problemset):
    """Represent an assignment (maybe send warning to student when close to deadlines)."""
    pass

class Submission:
    """Represent a submission from students."""
    
    def __init__(self, submission_id: str, student_id: str, problem_id: str, source_code: str, language: str):
        self.submission_id = submission_id
        self.student_id = student_id
        self.problem_id = problem_id
        self.source_code = source_code
        self.language = language
        self.status = "Pending"
        self.execution_time = 0.0
        self.memory_used = 0

    def update_status(self, new_status: str, time: float, mem_used: int):
        """Update final status for the submission."""
        pass

