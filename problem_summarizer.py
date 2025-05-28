import json
from gemini_api import call_gemini_api
import google.generativeai as genai


class ProblemSummarizer:
    def summarize_problem(self, problem_data: str) -> str:
        prompt = self._create_summarization_prompt(problem_data)
        response = call_gemini_api(prompt)
        result = self._extract_summary(response)

        return response

    def _create_summarization_prompt(self, problem_data: str) -> str:
        return f"""
Please summarize the following competitive programming problem statement in a clear, concise format that includes all essential information needed for code evaluation.

Original Problem Header:
- Maximum score: {problem_data["max_score"]}
- Time limit: {problem_data["time_limit"]} seconds
- Memory limit: {problem_data["memory_limit"]} MB
- Input file: {problem_data["input_file"]}
- Output file: {problem_data["output_file"]}

Original Problem Statement:
{problem_data["statement"]}

Please provide a summary that includes:
1. **Problem Score**: The maximum score for the problem
2. **Problem Statement**: The summarization of the statement
3. **Input Format**: What the input looks like
4. **Output Format**: What the expected output should be
5. **Constraints**: Important limits (time, space, value ranges, input file, output file, etc.)
6. **Example**: At least one input/output example if available. Do not explain the example, just provide it as is.

Format your response as a clear, structured summary that a code judge can use to evaluate solution correctness. Please do not include any additional explanations or comments beyond the summary itself. Keep it concise but complete - aim for 200-500 words.
"""

    def _extract_summary(self, response: str) -> str:
        if "PROBLEM SUMMARY:" in response:
            summary = response.split("PROBLEM SUMMARY:", 1)[1].strip()
        else:
            summary = response.strip()

        summary = (
            summary.replace("**", "")
            .replace("*", "")
            .replace("\n\n", "\n")
            .replace("  ", " ")
            .strip()
        )

        return summary


if __name__ == "__main__":
    with open("data.json", "r", encoding="utf8") as f:
        data = json.load(f)

    problem_id = "CAU4"
    problem_statement = """
Cho 𝑛 đồ vật, vật thứ 𝑖 có khối lượng là 𝑤𝑖 và giá trị là 𝑣𝑖
. Một cái túi có thể chịu
được khối lượng tối đa là 𝑊, nếu quá thì sẽ bị rách. Hãy tìm cách nhét một số đồ vật
vào trong túi sao cho túi không bị rách và tổng giá trị của các đồ vật nhét vào là lớn nhất
có thể.
Trang 3/3
Dữ liệu: Nhập từ bàn phím:
- Dòng đầu tiên chứa hai số nguyên 𝑛 và 𝑊 (1 ≤ 𝑛 ≤ 105
, 1 ≤ 𝑊 ≤ 109
).
- Trong 𝑛 dòng tiếp theo, dòng thứ 𝑖 chứa hai số nguyên 𝑤𝑖 và 𝑣𝑖
(
𝑊
3
≤ 𝑤𝑖 ≤
109
, 1 ≤ 𝑣𝑖 ≤ 109
).
Kết quả: Xuất ra file CAU4.OUT:
- Một dòng duy nhất chứa một số nguyên là tổng giá trị tối đa có thể đạt được.
Ví dụ:
Bàn phím CAU4.OUT
3 5
2 3
3 2
4 4
5
    """

    if problem_id not in data["problems_data"]:
        print(f"Problem ID {problem_id} not found in data.")
        exit(1)

    data["problems_data"][problem_id]["statement"] = problem_statement.strip()

    api_summarizer = ProblemSummarizer()
    api_summary = api_summarizer.summarize_problem(
        problem_data=data["problems_data"][problem_id]
    )

    data["problems_data"][problem_id]["statement"] = api_summary

    with open("data.json", "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
