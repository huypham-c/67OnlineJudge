import datetime

class User:
    """
    Base class representing a general user in the online judge system.

    Parameters
    ----------
    user_id : str
        Unique identifier for the user.
    username : str
        The display name and login name of the user.
    password_hash : str
        The encrypted/hashed password for authentication.
    """

    def __init__(self, user_id: str, username: str, password_hash: str):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
    
    def login(self) -> bool:
        """
        Authenticate the user.

        Returns
        -------
        bool
            True if login is successful, False otherwise.
        """
        pass
    
    def view_leaderboard(self):
        """View the current leaderboard of an active contest or assignment."""
        pass


class Student(User):
    """
    Class representing a student user, inherited from User.
    """

    def __init__(self, user_id: str, username: str, password_hash: str):
        super().__init__(user_id, username, password_hash)
        self.class_ids = set()

    def enroll(self, class_id: str):
        """
        Enroll the student in a new classroom.

        Parameters
        ----------
        class_id : str
            The unique identifier of the class to join.
        """
        self.class_ids.add(class_id)

    def submit_code(self, problem_id: str, source_code: str, language: str):
        """
        Submit source code to a specific problem.

        Parameters
        ----------
        problem_id : str
            The ID of the target problem.
        source_code : str
            The raw code string.
        language : str
            The programming language used.
        """
        pass


class Teacher(User):
    """
    Class representing a teacher user with administrative privileges over courses.
    Inherited from User.
    """

    def create_problem(self, title: str, description: str, time_limit: float, mem_limit: int):
        """
        Create a new coding problem in the system.

        Parameters
        ----------
        title : str
            The title of the problem.
        description : str
            The detailed problem statement.
        time_limit : float
            Execution time limit in seconds.
        mem_limit : int
            Memory limit in MB.
        """
        pass

    def create_problem_set(self, title: str, description: str, problemset: list, start_time: datetime.datetime, end_time: datetime.datetime):
        """
        Create a new Contest or Assignment.

        Parameters
        ----------
        title : str
            The name of the problem set.
        description : str
            Instructions or description for the set.
        problemset : list
            A list of problem IDs to be included.
        start_time : datetime.datetime
            Opening time.
        end_time : datetime.datetime
            Closing/Deadline time.
        """
        pass

    def manage_test_cases(self, problem_id: str):
        """
        Create, modify, or delete test cases for a specific problem.

        Parameters
        ----------
        problem_id : str
            The ID of the problem whose test cases are being managed.
        """
        pass

    def view_completions(self):
        """View the completion status of students in managed classes."""
        pass


class Admin(Teacher):
    """
    Class representing a system administrator with full access.
    Inherited from Teacher.
    """

    def create_user_account(self, role: str, username: str):
        """
        Create a new user account in the system.

        Parameters
        ----------
        role : str
            The role of the new user ('Student', 'Teacher', or 'Admin').
        username : str
            The desired username.
        """
        pass