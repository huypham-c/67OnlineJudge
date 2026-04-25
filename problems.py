import datetime
from typing import List, Dict, Optional

class Problem:
    """
    Represent a coding problem in the system, loaded from a directory structure.

    The system expects the following directory structure:
    - description.html: The problem statement in HTML format.
    - templates/: Contains starter code templates (template.py, template.cpp).
    - input/: Contains standard input files (.txt).
    - output/: Contains expected standard output files (.txt).

    Parameters
    ----------
    problem_id : str
        The unique identifier for the problem.
    title : str
        The display title of the problem.
    description : str
        The detailed problem statement.
    time_limits : dict, optional
        Dictionary defining time limits (in seconds) per language.
        Example: {"cpp": 1.0, "python": 2.0}.
    mem_limits : dict, optional
        Dictionary defining memory limits (in MB) per language.
        Example: {"cpp": 256, "python": 512}.
    allowed_lang : list, optional
        List of programming languages allowed for submissions.
        Defaults to ["cpp", "python"].
    """
    
    class TestCase:
        """
        Represent a single test case for a specific problem.

        Parameters
        ----------
        test_id : str
            Unique identifier for the test case (usually the filename).
        input_data : str
            The standard input (stdin) string to be fed into the program.
        expected_output : str
            The expected standard output (stdout) to verify correctness.
        is_hidden : bool, optional
            If True, this test case is used for actual grading and is hidden from the student. 
            Defaults to False.
        """

        def __init__(self, test_id: str, input_data: str, expected_output: str, is_hidden: bool = False):
            self.test_id = test_id
            self.input_data = input_data
            self.expected_output = expected_output
            self.is_hidden = is_hidden

    def __init__(self, problem_id: str, title: str, description: str, 
                 time_limits: dict = None, mem_limits: dict = None, 
                 allowed_lang: list = None):
        self.problem_id = problem_id
        self.title = title
        self.description = description
        
        self.time_limits = time_limits if time_limits else {"cpp": 1.0, "python": 2.0}
        self.mem_limits = mem_limits if mem_limits else {"cpp": 256, "python": 512}
        self.allowed_langs = allowed_lang if allowed_lang else ["cpp", "python"]
        
        self.test_cases: List['Problem.TestCase'] = []

class Problemset:
    """
    Base class representing a collection of problems (e.g., Contest, Assignment).

    Parameters
    ----------
    problemset_id : str
        Unique identifier for the problem set.
    title : str
        The display title of the problem set.
    start_time : datetime.datetime
        The timestamp when the problem set opens.
    end_time : datetime.datetime
        The timestamp when the problem set closes.
    """
    def __init__(self, problemset_id: str, title: str, start_time: datetime.datetime, end_time: datetime.datetime):
        self.problemset_id = problemset_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.problem_ids = set()

    def add_problem(self, problem: Problem):
        """
        Add a problem to this problem set.

        Parameters
        ----------
        problem : Problem
            The Problem object to be added.
        """
        pass

class Contest(Problemset):
    """
    Represent a competitive contest with a strict timeframe and public leaderboard.
    Inherits from Problemset.
    """
    pass

class Assignment(Problemset):
    """
    Represent a homework assignment. 
    May include features like deadline warnings. Inherits from Problemset.
    """
    pass

class Submission:
    """
    Represent a student's code submission to a specific problem.

    Parameters
    ----------
    submission_id : str
        Unique identifier for the submission.
    student_id : str
        The ID of the student who submitted the code.
    problem_id : str
        The ID of the problem being solved.
    source_code : str
        The raw source code submitted.
    language : str
        The programming language of the source code (e.g., 'python', 'cpp').
    """
    
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
        """
        Update the final grading status and performance metrics of the submission.

        Parameters
        ----------
        new_status : str
            The verdict (e.g., 'Accepted', 'Wrong Answer', 'Time Limit Exceeded').
        time : float
            The actual execution time in seconds.
        mem_used : int
            The actual memory consumed in MB.
        """
        pass