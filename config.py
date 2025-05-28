import json
from typing import Dict, Any


class Config:
    def __init__(self):
        self.data = self._load_json("data.json")
        self.config = self._load_json("config.json")
        self.key = self._load_json("key.json")

    def _load_json(self, filename: str) -> Dict[str, Any]:
        with open(filename, "r", encoding="utf8") as f:
            return json.load(f)

    @property
    def sheet_id(self) -> str:
        return self.data["sheet_id"]

    @property
    def contest_id(self) -> str:
        return self.data["contest_id"]

    @property
    def problems_data(self) -> Dict[str, Any]:
        return self.data["problems_data"]

    @property
    def round_digits(self) -> int:
        return self.config["round_digits"]

    @property
    def result_message(self) -> Dict[str, str]:
        return self.config["result_message"]

    @property
    def code_extension(self) -> Dict[str, str]:
        return self.config["code_extension"]

    @property
    def delay_time(self) -> float:
        return self.config["delay_time"]

    @property
    def reset_time(self) -> float:
        return self.config["reset_time"]

    @property
    def judge_id(self) -> str:
        return self.key["client_id"]

    @property
    def gemini_api_key(self) -> str:
        return self.key.get("gemini_api_key", "")
