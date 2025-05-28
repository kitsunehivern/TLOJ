import time
import gspread
from typing import List, Optional
from models import Submission, JudgeResult


class SheetManager:
    def __init__(
        self, key_file: str, sheet_id: str, contest_id: str, delay_time: float
    ):
        self.client = gspread.service_account(key_file)
        self.sheet = self.client.open_by_key(sheet_id).worksheet(contest_id)
        self.delay_time = delay_time

    def safe_request(self, request_func, *args, **kwargs):
        while True:
            try:
                return request_func(*args, **kwargs)
            except Exception as e:
                print(f"Sheet request error: {e}")
                time.sleep(self.delay_time)

    def get_submission(
        self, row: int, problems_data: dict, code_extension: dict
    ) -> Optional[Submission]:
        row_data = self.safe_request(self.sheet.row_values, row)

        if not row_data or len(row_data) < 5:
            return None

        problem_id = row_data[2][: row_data[2].find(".")]
        if problem_id not in problems_data:
            return None

        status = row_data[5] if len(row_data) >= 6 else ""
        judge = row_data[6] if len(row_data) >= 7 else ""

        return Submission(
            row=row,
            contestant=row_data[1],
            problem_id=problem_id,
            problem_name=problems_data[problem_id]["name"],
            language=row_data[3],
            extension=code_extension.get(row_data[3], "txt"),
            source_code=row_data[4],
            status=status,
            judge=judge,
        )

    def update_status(
        self, row: int, status: str, judge_id: str, judge_type: str = "Themis"
    ):
        self.safe_request(
            self.sheet.update, [[status, judge_id, judge_type]], f"F{row}:H{row}"
        )

    def update_single_cell(self, row: int, col: int, value: str):
        self.safe_request(self.sheet.update_cell, row, col, value)

    def update_results(self, row: int, result: JudgeResult, round_digits: int):
        formatted_log = self._format_log(result, round_digits)

        self.safe_request(
            self.sheet.update,
            [
                [
                    f"%.{round_digits}f" % result.total_points,
                    result.max_execution_time,
                    result.final_message,
                    formatted_log,
                ]
            ],
            f"I{row}:L{row}",
        )

    def get_empty_rows(self) -> List[int]:
        current_status = self.safe_request(self.sheet.col_values, 7)

        empty_rows = []
        for i in range(2, len(current_status) + 1):
            if current_status[i - 1] == "":
                empty_rows.append(i)

        empty_rows.append(len(current_status) + 1)

        return empty_rows

    def is_cell_empty(self, row: int, col: int) -> bool:
        return self.safe_request(self.sheet.cell, row, col).value is None

    def _format_log(self, result: JudgeResult, round_digits: int) -> str:
        log = f"Tổng: [{f'%.{round_digits}f' % result.total_points} điểm, {result.max_execution_time} ms] {result.final_message}"

        for i, test in enumerate(result.tests_result):
            log += f"\n#{i + 1}: [{f'%.{round_digits}f' % test.points} điểm, {test.execution_time} ms] {test.message}"

        return log
