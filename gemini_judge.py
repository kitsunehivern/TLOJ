import json
import time
from config import Config
from models import JudgeResult, TestResult, ProblemData
from gemini_api import call_gemini_api


class GeminiJudge:
    def __init__(self, result_messages: dict, round_digits: int):
        self.result_messages = result_messages
        self.round_digits = round_digits

    def judge_submission(
        self, source_code: str, language: str, problem_data: ProblemData
    ) -> JudgeResult:
        while True:
            try:
                prompt = self._create_judge_prompt(source_code, language, problem_data)
                response = call_gemini_api(prompt)

                if response is None:
                    raise Exception("Gemini API returned None response")

                result = self._parse_gemini_response(response, problem_data.time_limit)
                if result is None:
                    raise Exception("Failed to parse Gemini response")

                return result
            except Exception as e:
                print(f"Error during Gemini judging: {e}")

            time.sleep(Config().delay_time)
            print("Retrying Gemini judging...")

    def _create_judge_prompt(
        self, source_code: str, language: str, problem_data: ProblemData
    ) -> str:
        return f"""
You are a competitive programming judge. Please analyze the following code submission for correctness and quality, based on the provided problem.

Problem Statement and Constraints:
{problem_data.statement}

Source Code:
```{language}
{source_code}
````

Please evaluate this code and provide your judgment in the following JSON format:
{{
    "total_points": <float between 0 and {problem_data.max_score}>,
    "verdict": "AC" | "WA" | "RE" | "TLE" | "CE" | "NOF",
    "explanation": "<brief explanation of the verdict>",
    "test_cases": [
        {{
            "points": <float>,
            "verdict": "AC" | "WA" | "RE" | "TLE" | "CE" | "NOF",
            "estimated_execution_time": <int in milliseconds>
        }}
    ]
}}

Scoring Breakdown (Total: {problem_data.max_score}):

* 10% Code Quality: Clean, readable code with proper file handling (if applicable) and appropriate variable usage.
* 10% Compilability: Code compiles without errors.
* 20% Algorithmic Idea: The algorithm should reflect correct logic and effective problem-solving.
* 60% Test Simulation: Based on performance across at least 10 well-designed test cases.

Test Case Requirements:

* Provide a minimum of 10 test case evaluations.
* Use inputs that conform to the problem's constraints and format.
* Include a mix of random and edge cases.
* Each test case must contain:
  * points awarded (proportional to the 60% weight),
  * verdict (see criteria below),
  * estimated execution time in milliseconds.
* Execution time must be realistic and should reflect the time complexity of the algorithm. Do not use arbitrary or random values. The timing should be understandable to the user based on their algorithm.

Judging Criteria for Test Cases:

* AC (Accepted): Output is correct and within time/memory limits.
* WA (Wrong Answer): Output is incorrect.
* RE (Runtime Error): Program crashes or exits abnormally.
* TLE (Time Limit Exceeded): Execution exceeds the problem's time limit.
* CE (Compilation Error): Code fails to compile.
* NOF (No Output File): No output is produced when an output file is required.

Be thorough and objective. The explanation should clearly justify the total score and verdict. Keep it concise but informative.
"""

    def _parse_gemini_response(
        self, response: str, time_limit: float
    ) -> JudgeResult | None:
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                raise Exception("Invalid response format from Gemini")

            json_str = response[json_start:json_end]
            data = json.loads(json_str)

            total_points = round(float(data.get("total_points", 0)), self.round_digits)
            verdict = data.get("verdict", "RE")

            final_message = self.result_messages.get(
                verdict, self.result_messages["RE"]
            )

            tests_result = []
            test_cases = data.get("test_cases", [])

            if not test_cases:
                raise Exception("No test cases found in Gemini response")

            for i, test_case in enumerate(test_cases):
                test_points = round(
                    float(test_case.get("points", 0)), self.round_digits
                )
                test_verdict = test_case.get("verdict", "RE")
                test_message = self.result_messages.get(
                    test_verdict, self.result_messages["RE"]
                )

                execution_time = 0
                if test_verdict == "TLE":
                    execution_time = round(time_limit * 1000)
                else:
                    execution_time = int(test_case.get("estimated_execution_time", 0))

                tests_result.append(
                    TestResult(
                        points=test_points,
                        execution_time=execution_time,
                        message=test_message,
                    )
                )

            max_execution_time = max(
                (test.execution_time for test in tests_result), default=0
            )

            return JudgeResult(
                total_points=total_points,
                max_execution_time=max_execution_time,
                final_message=final_message,
                tests_result=tests_result,
            )

        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            return None
