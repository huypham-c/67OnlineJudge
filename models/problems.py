import os
import datetime
import shutil
from typing import List, Dict, Optional, Set

PROBLEM_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "problems")

class Problem:
    """
    Represent a coding problem in the system, loaded from a directory structure.

    The system expects the following directory structure:
    - description.html: The problem statement in HTML format.
    - banned_word.txt: List of restricted keywords.
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
        input_file : str
            The physical path to the standard input (stdin) file.
        output_file : str
            The physical path to the expected standard output (stdout) file.
        """
        def __init__(self, test_id: str, input_file: str, output_file: str):
            self.test_id = test_id
            self.input_file = input_file
            self.output_file = output_file

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

    @property
    def folder_path(self) -> str:
        """
        Dynamically compute the storage path matching the current problem_id.
        
        Returns
        -------
        str
            The absolute path to the problem's physical data directory.
        """
        return os.path.join(PROBLEM_DATA_DIR, self.problem_id)

    def save_problem_data(self, html_content: str, testcases: List[tuple], banned_words: List[str]):
        """
        Save physical files for the problem to the disk.
        
        Initializes or overwrites the problem directory, generating the description,
        banned words list, and individual input/output files for each test case.
        
        Parameters
        ----------
        html_content : str
            The HTML content of the problem description.
        testcases : List[tuple]
            A list of tuples containing (input_data, expected_output).
        banned_words : List[str]
            A list of banned words/keywords for this problem.
        """
        os.makedirs(self.folder_path, exist_ok=True)
        
        input_dir = os.path.join(self.folder_path, "input")
        output_dir = os.path.join(self.folder_path, "output")
        
        if os.path.exists(input_dir):
            shutil.rmtree(input_dir)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            
        os.makedirs(input_dir)
        os.makedirs(output_dir)

        with open(os.path.join(self.folder_path, "description.html"), "w", encoding="utf-8") as f:
            f.write(html_content)
            
        with open(os.path.join(self.folder_path, "banned_word.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(banned_words))

        for i, (inp, out) in enumerate(testcases, start=1):
            with open(os.path.join(input_dir, f"{i}.txt"), "w", encoding="utf-8") as f:
                f.write(inp)
            with open(os.path.join(output_dir, f"{i}.txt"), "w", encoding="utf-8") as f:
                f.write(out)

    def get_banned_words(self) -> List[str]:
        """
        Retrieve the list of restricted keywords from local storage.

        Reads the physical 'banned_word.txt' file linked to the current problem 
        directory to enforce constraints during code submission.

        Returns
        -------
        List[str]
            A comprehensive list of unauthorized code segments or keywords.
        """
        banned_path = os.path.join(self.folder_path, "banned_word.txt")
        if not os.path.exists(banned_path):
            return []
        with open(banned_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def load_test_cases(self):
        """
        Scan and hydrate test cases from the physical problem directory.

        Dynamically iterates over the 'input' and 'output' folders to map matching 
        pairs of test configurations and appends them to the problem instance.
        """
        self.test_cases = []
        input_dir = os.path.join(self.folder_path, "input")
        output_dir = os.path.join(self.folder_path, "output")
        
        if not os.path.exists(input_dir) or not os.path.exists(output_dir):
            return

        for filename in os.listdir(input_dir):
            if filename.endswith(".txt"):
                base_name = filename[:-4] 
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename)
                
                if os.path.exists(output_path):
                    self.test_cases.append(self.TestCase(
                        test_id=base_name,
                        input_file=input_path,
                        output_file=output_path,
                    ))

class Problemset:
    """
    Represent a collection of problems (e.g., Contest, Assignment).

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
    set_type : str, optional
        The category of the problem set, defaults to 'assignment'.
    """
    def __init__(self, problemset_id: str, title: str, start_time: datetime.datetime, end_time: datetime.datetime, set_type: str = "assignment"):
        self.problemset_id = problemset_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.set_type = set_type
        self.problem_ids: Set[str] = set()

    def add_problem(self, problem_id: str):
        """
        Add a problem to this problem set.

        Parameters
        ----------
        problem_id : str
            The ID of the problem to be added.
        """
        self.problem_ids.add(problem_id)

    def generate_leaderboard(self) -> dict:
        """
        Calculate and generate the current leaderboard for this problem set.

        Returns
        -------
        dict
            A structured dictionary containing the ranked students and their scores.
        """
        pass

    def get_completion_status(self) -> dict:
        """
        Generate a report of student completion statuses for this problem set.

        Returns
        -------
        dict
            A mapping of student IDs to their completion status (e.g., done, pending, late).
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
        self.status = new_status
        self.execution_time = time
        self.memory_used = mem_used