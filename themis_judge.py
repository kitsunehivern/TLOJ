from models import JudgeResult, TestResult, ProblemData


class ThemisJudge:
    def __init__(self, result_messages: dict, round_digits: int):
        self.result_messages = result_messages
        self.round_digits = round_digits

    def parse_log(self, log: str, problem_data: ProblemData) -> JudgeResult:
        logs = log.split("\n")

        problem_name, language = logs[1].split(".")

        assert problem_name == problem_data.name, "Problem name does not match"

        total_points = 0
        max_execution_time = 0
        final_message = None
        tests_result = []

        if self.result_messages["CE"] in log:
            final_message = self.result_messages["CE"]
            message = self._parse_compilation_error(logs, problem_name, language)
            tests_result.append(TestResult(points=0, execution_time=0, message=message))
        else:
            total_points = round(
                float(logs[0].split(" ")[-1].replace(",", ".")), self.round_digits
            )

            tests_result, max_execution_time, final_message = self._parse_test_results(
                logs, problem_data.time_limit
            )

        total_points = round(total_points, self.round_digits)

        return JudgeResult(
            total_points=total_points,
            max_execution_time=max_execution_time,
            final_message=final_message,
            tests_result=tests_result,
        )

    def _parse_compilation_error(
        self, logs: list, problem_name: str, language: str
    ) -> str:
        message = self.result_messages["CE"]
        for i in range(3, len(logs) - 1):
            if logs[i] == "Dịch lỗi!":
                break

            if logs[i].split(".")[0] == problem_name:
                logs[i] = logs[i].replace(problem_name, "main", 1)
            elif logs[i].split(" ")[0] == "Error:" and language == "pas":  # Pascal
                continue

            message += "\n" + logs[i]

        return message[:10000] + "..." if len(message) > 10000 else message

    def _parse_test_results(self, logs: list, time_limit: float) -> tuple:
        tests_result = []
        max_execution_time = 0
        final_message = None

        i = 1
        while i < len(logs) and chr(0x2023) not in logs[i]:
            i += 1

        while i < len(logs):
            j = i + 1
            while j < len(logs) and chr(0x2023) not in logs[j]:
                j += 1
            j -= 1

            points = round(
                float(logs[i].split(" ")[-1].replace(",", ".")), self.round_digits
            )
            execution_time = 0
            message = self.result_messages["AC"]
            exit_code = 0

            for k in range(i, j + 1):
                words = logs[k].split(" ")

                for message_code in ["WA", "RE", "TLE", "NOF"]:
                    if (
                        self.result_messages[message_code] in logs[k]
                        and message == self.result_messages["AC"]
                    ):
                        message = self.result_messages[message_code]

                if words[:2] == ["Thời", "gian"]:
                    execution_time = round(float(words[-2].replace(",", ".")) * 1000)

                for idx in range(len(words) - 3):
                    if words[idx : idx + 2] == ["exit", "code:"]:
                        exit_code = int(words[idx + 2])

            if message == self.result_messages["TLE"]:
                execution_time = round(time_limit * 1000)

            max_execution_time = max(max_execution_time, execution_time)

            if message != self.result_messages["AC"] and final_message is None:
                final_message = message

            if message == self.result_messages["RE"]:
                message += f" (exit code: {exit_code})"

            tests_result.append(
                TestResult(
                    points=points, execution_time=execution_time, message=message
                )
            )

            i = j + 1

        if final_message is None:
            final_message = self.result_messages["AC"]

        return tests_result, max_execution_time, final_message
