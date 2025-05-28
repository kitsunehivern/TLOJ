import os
import time
from models import Submission, JudgeResult, ProblemData
from themis_judge import ThemisJudge
from gemini_judge import GeminiJudge
from sheet_manager import SheetManager
from config import Config


class JudgeManager:
    def __init__(self):
        self.config = Config()
        self.sheet_manager = SheetManager(
            "key.json",
            self.config.sheet_id,
            self.config.contest_id,
            self.config.delay_time,
        )

        self.themis_judge = ThemisJudge(
            self.config.result_message, self.config.round_digits
        )

        self.gemini_judge = GeminiJudge(
            self.config.result_message,
            self.config.round_digits,
        )

        self.current_row = 0
        self.judge_done = True
        self.out_of_submission = False
        self.last_reset = -self.config.reset_time
        self.submission_status = ""
        self.missed_rows = []

        print("Judge initialized successfully")

    def run(self):
        print("Starting judge...")

        while True:
            time.sleep(self.config.delay_time)

            if self._should_reset():
                self._reset_judge()

            if self.judge_done:
                if not self._find_next_submission():
                    continue

            submission = self.sheet_manager.get_submission(
                self.current_row, self.config.problems_data, self.config.code_extension
            )

            if submission is None:
                self.out_of_submission = True
                print("Waiting for new submission...")
                continue
            else:
                self.out_of_submission = False

            print(f"Submission #{self.current_row - 1}:", self.submission_status)

            self._process_submission(submission)

    def _should_reset(self) -> bool:
        return (
            self.out_of_submission or self.judge_done
        ) and time.time() > self.last_reset + self.config.reset_time

    def _reset_judge(self):
        print("Resetting the judge...")

        self.missed_rows = self.sheet_manager.get_empty_rows()

        if self.missed_rows:
            self.current_row = self.missed_rows.pop(0)
        else:
            self.current_row = 2

        self.submission_status = "Queuing"
        self.judge_done = False
        self.last_reset = time.time()

        print("Judge resetted")

    def _find_next_submission(self) -> bool:
        print("Finding next submission...")

        while True:
            if self.missed_rows:
                self.current_row = self.missed_rows.pop(0)
            else:
                self.current_row += 1

            if self.sheet_manager.is_cell_empty(self.current_row, 7):
                break

        print("Next submission found")
        self.judge_done = False
        self.submission_status = "Queuing"
        return True

    def _process_submission(self, submission: Submission):
        if submission.status == "":
            self._initialize_submission(submission)
        elif submission.judge == self.config.judge_id:
            if submission.status == "Đang chờ":
                self._start_judging(submission)
            elif submission.status == "Đang chấm":
                self._complete_judging(submission)
        else:
            self.judge_done = True
            self.submission_status = "Skipped"
            print("Submission is judged by another judge")

    def _initialize_submission(self, submission: Submission):
        problem_data = ProblemData.from_dict(
            self.config.problems_data[submission.problem_id]
        )
        judge_type = problem_data.judge_type

        self.sheet_manager.update_status(
            submission.row, "Đang chờ", self.config.judge_id, judge_type
        )

        if judge_type == "Themis":
            os.makedirs("Submissions", exist_ok=True)
            with open(
                f"Submissions/{submission.submission_name}", "w", encoding="utf8"
            ) as f:
                f.write(submission.source_code)

        self.submission_status = "Waiting"
        print("Change status to Waiting")

    def _start_judging(self, submission: Submission):
        problem_data = ProblemData.from_dict(
            self.config.problems_data[submission.problem_id]
        )

        if problem_data.judge_type == "Themis":
            if not os.path.exists(f"Submissions/{submission.submission_name}"):
                self.sheet_manager.update_single_cell(submission.row, 6, "Đang chấm")
                self.submission_status = "Judging"
                print("Change status to Judging")
        else:
            self.sheet_manager.update_single_cell(submission.row, 6, "Đang chấm")
            self._judge_with_gemini(submission, problem_data)

    def _complete_judging(self, submission: Submission):
        problem_data = ProblemData.from_dict(
            self.config.problems_data[submission.problem_id]
        )

        if problem_data.judge_type == "Themis":
            self._complete_themis_judging(submission, problem_data)

    def _complete_themis_judging(
        self, submission: Submission, problem_data: ProblemData
    ):
        log_file = f"Submissions/Logs/{submission.submission_name}.log"

        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf8") as f:
                result = self.themis_judge.parse_log(f.read(), problem_data)

            self._finalize_judging(submission, result)

    def _judge_with_gemini(self, submission: Submission, problem_data: ProblemData):
        if not self.gemini_judge:
            print("Gemini API key not configured!")
            return

        print("Judging with Gemini API...")
        result = self.gemini_judge.judge_submission(
            submission.source_code, submission.language, problem_data
        )
        self._finalize_judging(submission, result, is_gemini=True)

    def _finalize_judging(
        self, submission: Submission, result: JudgeResult, is_gemini: bool = False
    ):
        self.sheet_manager.update_single_cell(submission.row, 6, "Đã chấm")
        self.sheet_manager.update_results(
            submission.row, result, self.config.round_digits
        )

        self.judge_done = True
        self.submission_status = "Judged"

        judge_type = "Gemini" if is_gemini else "Themis"
        print(f"Change status to Judged ({judge_type})")


if __name__ == "__main__":
    judge = JudgeManager()
    judge.run()
