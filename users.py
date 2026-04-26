import datetime
import hashlib
import uuid
from typing import Set, List
from problems import Submission, Problem, Problemset

class User:
    """
    Base class representing a general user in the judge system.

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

    def verify_password(self, raw_password: str) -> bool:
        """
        Verify if the provided raw password matches the stored hash.

        Parameters
        ----------
        raw_password : str
            The plain text password entered by the user.

        Returns
        -------
        bool
            True if the password is correct, False otherwise.
        """
        salted_password = raw_password + self.username
        hashed_input = hashlib.sha256(salted_password.encode('utf-8')).hexdigest()
        return self.password_hash == hashed_input
    
    def submit_code(self, problem_id: str, source_code: str, language: str) -> Submission:
        """
        Create a new submission object for a specific problem.

        Parameters
        ----------
        problem_id : str
            The ID of the target problem.
        source_code : str
            The raw code string.
        language : str
            The programming language used.

        Returns
        -------
        Submission
            A newly initialized Submission object.
        """
        submission_id = str(uuid.uuid4())
        new_submission = Submission(
            submission_id=submission_id, 
            student_id=self.user_id, 
            problem_id=problem_id, 
            source_code=source_code, 
            language=language
        )
        return new_submission


class Student(User):
    """
    Class representing a student user, inherited from User.
    """

    def __init__(self, user_id: str, username: str, password_hash: str):
        super().__init__(user_id, username, password_hash)
        self.class_ids: Set[str] = set()


class Teacher(User):
    """
    Class representing a teacher user with administrative privileges over courses.
    Inherited from User.
    """

    def create_classroom(self, class_name: str) -> 'Classroom':
        """
        Factory method to generate a new Classroom object.

        Parameters
        ----------
        class_name : str
            The display name of the classroom to be created.

        Returns
        -------
        Classroom
            A newly initialized Classroom object managed by this teacher.
        """
        class_id = f"CLASS_{str(uuid.uuid4())}"
        return Classroom(class_id=class_id, teacher_id=self.user_id, class_name=class_name)

    def create_problem(self, title: str, description: str, time_limits: dict, mem_limits: dict, allowed_langs: list) -> Problem:
        """
        Create a new coding problem in the system.

        Parameters
        ----------
        title : str
            The title of the problem.
        description : str
            The detailed problem statement.
        time_limits : dict
            Dictionary defining execution time limits in seconds per language.
        mem_limits : dict
            Dictionary defining memory limits in MB per language.
        allowed_langs : list
            List of programming languages allowed for submissions.

        Returns
        -------
        Problem
            A newly initialized Problem object.
        """
        problem_id = f"PROB_{str(uuid.uuid4())}"
        return Problem(
            problem_id=problem_id, 
            title=title, 
            description=description, 
            time_limits=time_limits, 
            mem_limits=mem_limits, 
            allowed_lang=allowed_langs
        )

    def create_problem_set(self, title: str, description: str, problemset: list, start_time: datetime.datetime, end_time: datetime.datetime) -> Problemset:
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

        Returns
        -------
        Problemset
            A newly initialized Problemset object.
        """
        ps_id = f"SET_{str(uuid.uuid4())}"
        new_set = Problemset(
            problemset_id=ps_id, 
            title=title, 
            start_time=start_time, 
            end_time=end_time
        )
        for prob_id in problemset:
            new_set.add_problem(prob_id)
        return new_set

    def manage_test_cases(self, problem_id: str):
        """
        Create, modify, or delete test cases for a specific problem.

        Parameters
        ----------
        problem_id : str
            The ID of the problem whose test cases are being managed.
        """
        pass
    

class Admin(Teacher):
    """
    Class representing a system administrator with full access.
    Inherited from Teacher.
    """

    def create_user_account(self, role: str, username: str, raw_password: str) -> User:
        """
        Factory method to generate a new User account.

        Parameters
        ----------
        role : str
            The role of the new user (e.g., 'student', 'teacher', 'admin').
        username : str
            The desired username for the new account.
        raw_password : str
            The plain text password, which will be hashed before storage.

        Returns
        -------
        User
            A newly initialized User (or Student/Teacher/Admin) object.
        """
        user_id = str(uuid.uuid4())
        
        salted_password = raw_password + username
        pwd_hash = hashlib.sha256(salted_password.encode('utf-8')).hexdigest()

        if role == 'student':
            return Student(user_id, username, pwd_hash)
        elif role == 'teacher':
            return Teacher(user_id, username, pwd_hash)
        
        return Admin(user_id, username, pwd_hash)

class Classroom:
    """
    Represent a classroom managed by a teacher.

    Parameters
    ----------
    class_id : str
        Unique identifier for the classroom.
    teacher_id : str
        The ID of the teacher who owns and manages this class.
    class_name : str
        The display name of the classroom.
    """

    def __init__(self, class_id: str, teacher_id: str, class_name: str):
        self.class_id = class_id
        self.teacher_id = teacher_id
        self.class_name = class_name
        self.student_ids: Set[str] = set()
        self.problemset_ids: Set[str] = set()

    def add_student(self, student_id: str):
        """
        Add a student to the classroom.

        Parameters
        ----------
        student_id : str
            The ID of the student to be enrolled.
        """
        self.student_ids.add(student_id)

    def assign_problemset(self, problemset_id: str):
        """
        Assign a new problem set (assignment/contest) to this classroom.

        Parameters
        ----------
        problemset_id : str
            The ID of the problem set to be assigned.
        """
        self.problemset_ids.add(problemset_id)