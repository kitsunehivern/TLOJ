import os
import json
import gspread
import mosspy
import shutil

userid = 908497776


def main():
    with open("data.json", "r", encoding="utf8") as f:
        data = json.load(f)

        sheet_id = data["sheet_id"]
        contest_id = data["contest_id"]

        problems_data = data["problems_data"]

    with open("key.json", "r") as f:
        key = json.load(f)

        judge_id = key["client_id"]

    print("Connecting to Google Sheets...")

    client = gspread.service_account("key.json")
    sheet = client.open_by_key(sheet_id).worksheet("Registrants")

    print("Connected to Google Sheets")

    data = sheet.get_all_records()
    contestants = {}
    for row in data[1:]:
        contestants[row["Email Address"]] = (
            "["
            + row["🌸 Bạn đến từ đâu nè?"]
            + "] "
            + row["🌸 Họ và tên đầy đủ của bạn là gì?"]
        )

    os.mkdir("Moss", exist_ok=True)
    shutil.rmtree("Moss", ignore_errors=True)

    os.chdir("Contestants")
    all_problems = []
    for folder in os.listdir():
        os.chdir(folder)
        for file in os.listdir():
            if file.endswith(".cpp"):
                all_problems.append(file[:-4].upper())
        os.chdir("..")

    all_problems = list(set(all_problems))

    print(all_problems)

    os.chdir("..\\Moss")
    for problem in all_problems:
        os.system("mkdir " + problem)
    os.chdir("..\\Contestants")
    for folder in os.listdir():
        os.chdir(folder)
        for file in os.listdir():
            if (file.endswith(".cpp")) and folder in contestants:
                os.system(
                    "copy "
                    + file
                    + ' "..\\..\\Moss\\'
                    + file[:-4].upper()
                    + "\\"
                    + contestants[folder]
                    + '"'
                )
        os.chdir("..")
    os.chdir("..\\Moss")

    moss_url = []
    for problem in all_problems:
        os.chdir(problem)

        print("Checking " + problem + " submissions...")

        moss = mosspy.Moss(userid, "cpp")
        moss.addFilesByWildcard("*")
        url = moss.send()
        moss_url.append({"problem": problem, "url": url})

        moss.saveWebPage(url, "report.html")

        print("Report saved to report.html")

        os.chdir("..")

    for moss in sorted(moss_url, key=lambda x: x["problem"]):
        print(moss["problem"] + ": " + moss["url"])


if __name__ == "__main__":
    main()
