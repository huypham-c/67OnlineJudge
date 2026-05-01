import os
import time
import subprocess
import tempfile
import shutil
from typing import Dict, Any
from models.problems import Submission, Problem

class JudgeEngine:
    """
    The core execution engine that safely evaluates submissions 
    using Docker containers with partial grading support.

    Parameters
    ----------
    image_name : str, optional
        The name and tag of the Docker image used for the sandbox environment. 
        Defaults to 'judge-sandbox:latest'.
    """

    def __init__(self, image_name: str = "judge-sandbox:latest"):
        self.image_name = image_name

    def evaluate_submission(self, submission: 'Submission', problem: 'Problem') -> Dict[str, Any]:
        """
        Route the submission to the appropriate Docker evaluator based on the programming language.

        Parameters
        ----------
        submission : Submission
            The submission object containing the source code and language.
        problem : Problem
            The problem object containing test cases, time limits, and memory limits.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing the final verdict, execution time, passed cases, 
            and detailed results for each test case.
        """
        if submission.language not in problem.allowed_langs:
            submission.update_status("Language Not Allowed", 0.0, 0)
            return {"verdict": "Language Not Allowed", "time_used": 0.0, "passed_cases": 0}

        if submission.language == "python":
            return self._eval_python(submission, problem)
        elif submission.language == "cpp":
            return self._eval_cpp(submission, problem)
        else:
            submission.update_status("System Error", 0.0, 0)
            return {"verdict": "Unsupported Language"}

    def _eval_cpp(self, submission: 'Submission', problem: 'Problem') -> Dict[str, Any]:
        """
        Handle compilation and secure execution for C++ submissions.

        Utilizes Docker volumes to isolate the compilation process and routes 
        standard I/O dynamically to prevent unauthorized system access.

        Parameters
        ----------
        submission : Submission
            The submission instance holding the raw C++ code.
        problem : Problem
            The reference problem containing time, memory limits, and test cases.

        Returns
        -------
        Dict[str, Any]
            A detailed diagnostic dictionary including the final verdict, 
            time consumed, and specific breakdown per test case.
        """
        current_time_limit = problem.time_limits.get(submission.language, 1.0)
        current_mem_limit = problem.mem_limits.get(submission.language, 256)

        host_dir = tempfile.mkdtemp()
        os.chmod(host_dir, 0o777)
        code_path = os.path.join(host_dir, "solution.cpp")
        
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(submission.source_code)
        os.chmod(code_path, 0o777)

        final_verdict = "Accepted"
        final_time = 0.0
        passed_cases = 0
        test_details = []

        try:
            try:
                compile_cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{host_dir}:/sandbox",
                    self.image_name,
                    "g++", "-O3", "-w", "/sandbox/solution.cpp", "-o", "/sandbox/solution.out"
                ]
                compile_process = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=10.0)
                
                if compile_process.returncode != 0:
                    submission.update_status("Compilation Error", 0.0, 0)
                    return {"verdict": "Compilation Error", "error_message": compile_process.stderr}
                    
            except subprocess.TimeoutExpired:
                submission.update_status("Compilation Time Limit Exceeded", 0.0, 0)
                return {"verdict": "Compilation Time Limit Exceeded"}

            for tc in problem.test_cases:
                start_time = time.time()
                
                with open(tc.input_file, "r", encoding="utf-8") as f:
                    input_data = f.read()
                with open(tc.output_file, "r", encoding="utf-8") as f:
                    expected_output = f.read().strip()

                tc_result = {
                    "test_id": tc.test_id,
                    "verdict": "Pending",
                    "time_used": 0.0
                }

                try:
                    run_cmd = [
                        "docker", "run", "--rm",
                        "--network", "none",
                        "--memory", f"{current_mem_limit}m",
                        "-i",
                        "-v", f"{host_dir}:/sandbox",
                        self.image_name,
                        "/sandbox/solution.out"
                    ]
                    
                    result = subprocess.run(
                        run_cmd,
                        input=input_data,
                        text=True,
                        capture_output=True,
                        timeout=current_time_limit + 1.0 
                    )
                    
                    execution_time = time.time() - start_time
                    final_time = max(final_time, execution_time)
                    tc_result["time_used"] = round(execution_time, 3)

                    if result.returncode != 0:
                        tc_verdict = "Memory Limit Exceeded" if result.returncode == 137 else "Runtime Error"
                        tc_result["verdict"] = tc_verdict
                        if tc_verdict == "Runtime Error" and result.stderr:
                            tc_result["error_message"] = result.stderr.strip()
                        test_details.append(tc_result)
                        if final_verdict == "Accepted":
                            final_verdict = tc_verdict
                        break

                    if result.stdout.strip() != expected_output:
                        tc_result["verdict"] = "Wrong Answer"
                        test_details.append(tc_result)
                        if final_verdict == "Accepted":
                            final_verdict = "Wrong Answer"
                        continue
                    
                    tc_result["verdict"] = "Accepted"
                    test_details.append(tc_result)
                    passed_cases += 1

                except subprocess.TimeoutExpired:
                    final_time = current_time_limit
                    tc_result["time_used"] = current_time_limit
                    tc_result["verdict"] = "Time Limit Exceeded"
                    test_details.append(tc_result)
                    if final_verdict == "Accepted":
                        final_verdict = "Time Limit Exceeded"
                    break

        finally:
            if os.path.exists(host_dir):
                shutil.rmtree(host_dir)

        submission.update_status(final_verdict, final_time, 0)
        return {
            "verdict": final_verdict, 
            "time_used": final_time, 
            "passed_cases": passed_cases,
            "total_cases": len(problem.test_cases),
            "details": test_details
        }

    def _eval_python(self, submission: 'Submission', problem: 'Problem') -> Dict[str, Any]:
        """
        Handle execution and partial grading for Python 3 submissions.

        Spawns ephemeral Docker containers with constrained memory and time 
        limits to evaluate the interpreted script safely.

        Parameters
        ----------
        submission : Submission
            The submission instance containing the raw Python script.
        problem : Problem
            The reference problem defining test inputs and expected outputs.

        Returns
        -------
        Dict[str, Any]
            A detailed diagnostic dictionary mapping the execution outcome.
        """
        current_time_limit = problem.time_limits.get(submission.language, 2.0)
        current_mem_limit = problem.mem_limits.get(submission.language, 512)
        
        host_dir = tempfile.mkdtemp()
        os.chmod(host_dir, 0o777)
        code_path = os.path.join(host_dir, "solution.py")
        
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(submission.source_code)
        os.chmod(code_path, 0o777)

        final_verdict = "Accepted"
        final_time = 0.0
        passed_cases = 0
        test_details = [] 

        try:
            for tc in problem.test_cases:
                start_time = time.time()
                
                with open(tc.input_file, "r", encoding="utf-8") as f:
                    input_data = f.read()
                with open(tc.output_file, "r", encoding="utf-8") as f:
                    expected_output = f.read().strip()

                tc_result = {
                    "test_id": tc.test_id,
                    "verdict": "Pending",
                    "time_used": 0.0
                }

                try:
                    run_cmd = [
                        "docker", "run", "--rm",
                        "--network", "none",
                        "--memory", f"{current_mem_limit}m",
                        "-i",
                        "-v", f"{host_dir}:/sandbox",
                        self.image_name,
                        "python3", "/sandbox/solution.py"
                    ]

                    result = subprocess.run(
                        run_cmd,
                        input=input_data,
                        text=True,
                        capture_output=True,
                        timeout=current_time_limit + 1.0
                    )
                    
                    execution_time = time.time() - start_time
                    final_time = max(final_time, execution_time)
                    tc_result["time_used"] = round(execution_time, 3)

                    if result.returncode != 0:
                        tc_verdict = "Memory Limit Exceeded" if result.returncode == 137 else "Runtime Error"
                        tc_result["verdict"] = tc_verdict
                        if tc_verdict == "Runtime Error" and result.stderr:
                            tc_result["error_message"] = result.stderr.strip()
                        test_details.append(tc_result)
                        if final_verdict == "Accepted":
                            final_verdict = tc_verdict
                        break

                    if result.stdout.strip() != expected_output:
                        tc_result["verdict"] = "Wrong Answer"
                        test_details.append(tc_result)
                        if final_verdict == "Accepted":
                            final_verdict = "Wrong Answer"
                        continue
                    
                    tc_result["verdict"] = "Accepted"
                    test_details.append(tc_result)
                    passed_cases += 1

                except subprocess.TimeoutExpired:
                    final_time = current_time_limit
                    tc_result["time_used"] = current_time_limit
                    tc_result["verdict"] = "Time Limit Exceeded"
                    test_details.append(tc_result)
                    if final_verdict == "Accepted":
                        final_verdict = "Time Limit Exceeded"
                    break

        finally:
            if os.path.exists(host_dir):
                shutil.rmtree(host_dir)

        submission.update_status(final_verdict, final_time, 0)
        
        return {
            "verdict": final_verdict, 
            "time_used": final_time, 
            "passed_cases": passed_cases,
            "total_cases": len(problem.test_cases),
            "details": test_details
        }