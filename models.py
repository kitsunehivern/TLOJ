from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class TestResult:
    points: float
    execution_time: int
    message: str


@dataclass
class JudgeResult:
    total_points: float
    max_execution_time: int
    final_message: str
    tests_result: List[TestResult]


@dataclass
class Submission:
    row: int
    contestant: str
    problem_id: str
    problem_name: str
    language: str
    extension: str
    source_code: str
    status: str
    judge: str

    @property
    def submission_name(self) -> str:
        return f"{str(self.row - 1).zfill(4)}[{self.contestant}][{self.problem_name}].{self.extension}"


@dataclass
class ProblemData:
    name: str
    judge_type: str  # "Themis" or "Gemini"
    max_score: float
    time_limit: float
    memory_limit: int
    input_file: str
    output_file: str
    statement: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProblemData":
        return cls(
            name=data["name"],
            judge_type=data.get("judge_type", "Themis"),
            max_score=data.get("max_score", 100.0),
            time_limit=data.get("time_limit", 1.0),
            memory_limit=data.get("memory_limit", 256),
            input_file=data.get("input_file", "stdin"),
            output_file=data.get("output_file", "stdout"),
            statement=data.get("statement", ""),
        )
