import os
import time
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

with open('config.json', 'r', encoding = 'utf8') as f:
    config = json.load(f)

    sheet_name = config['sheet_name']

    problems_data = config['problems_data']

    result_message = config['result_message']
    code_extension = config['code_extension']

    delay_time = config['delay_time']
    reset_time = config['reset_time']

with open('key.json', 'r') as f:
    key = json.load(f)

    judge_id = key['client_id']

print("Sheet name:", sheet_name)
print("Judge ID:", judge_id)

scope = ["https://spreadsheets.google.com/feeds", 
         "https://www.googleapis.com/auth/spreadsheets", 
         "https://www.googleapis.com/auth/drive.file", 
         "https://www.googleapis.com/auth/drive"]

print("Connecting to Google Sheets...")

creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
client = gspread.authorize(creds)
sheet = client.open(sheet_name).worksheet("Submissions")

print("Connected to Google Sheets")

def log_parser(log, problem_data):
    logs = log.split('\n')

    problem_name, language = logs[1].split('.')

    assert problem_name == problem_data['name'], "Problem name does not match"

    total_points = 0
    max_execution_time = 0
    final_message = result_message['AC']
    tests_result = []
    failed_test = '-'
    if result_message['CE'] in log:
        final_message = result_message['CE'] + '\n'
        for i in range(3, len(logs) - 1):
            if logs[i] == "Dịch lỗi!":
                break

            if logs[i].split('.')[0] == problem_name:
                logs[i].replace(problem_name, 'main', 1)
            elif logs[i].split(' ')[0] == 'Error:' and language == 'pas': # Pascal, why?
                continue

            final_message += logs[i] + '\n'
    else:
        total_points = round(float(logs[0].split(' ')[-1].replace(',', '.')), 2)

        i = logs.index("") + 1
        tests_count = 0
        while i < len(logs):
            j = i + 1
            while j < len(logs) and problem_name not in logs[j]:
                j += 1
            j -= 1

            tests_count += 1

            points = round(float(logs[i].split(' ')[-1].replace(',', '.')), 2)
            execution_time = 0
            message = result_message['AC']
            exit_code = 0
            for k in range(i, j + 1):
                words = logs[k].split(' ')

                for message_code in ['WA', 'RE', 'TLE']:
                    if result_message[message_code] in logs[k] and message == result_message['AC']:
                        message = result_message[message_code]

                if words[:2] == ['Thời', 'gian']:
                    execution_time = round(float(words[-2].replace(',', '.')) * 1000)

                for i in range(len(words) - 3):
                    if words[i:i + 2] == ['exit', 'code:']:
                        exit_code = int(words[i + 2])

            if message == result_message['TLE']:
                execution_time = round(problem_data['time_limit'] * 1000)

            max_execution_time = max(max_execution_time, execution_time)
            
            if message != result_message['AC'] and failed_test == '-':
                failed_test = str(tests_count)
                final_message = message
            
            if message == result_message['RE']:
                message += f'(exit code: {exit_code})'

            tests_result.append({'points': points, 'execution_time': execution_time, 'message': message})

            i = j + 1

    total_points = round(total_points, 2)
    final_message = final_message[:-1]

    return total_points, max_execution_time, final_message, failed_test, tests_result

def format_log(total_points, max_execution_time, final_message, tests_result):
    log = f"Tổng [{total_points:g} điểm, {max_execution_time} ms]: {final_message}"
    for i in range(len(tests_result)):
        log += f"\n#{i + 1} [{tests_result[i]['points']:g} điểm, {tests_result[i]['execution_time']} ms]: {tests_result[i]['message']}"

    return log

def send_request(request_func, *args):
    while True:
        try:
            return request_func(*args)
        except Exception as e:
            print(e)
            time.sleep(delay_time)

current_row = 0
judge_done = True
out_of_submission = False
last_reset = -reset_time
while True:
    time.sleep(delay_time)

    if (out_of_submission or judge_done) and time.time() > last_reset + reset_time:
        print("Resetting the judge...")
        current_status = send_request(sheet.col_values, 7)

        missed_rows = []
        for i in range(2, len(current_status) + 1):
            if current_status[i - 1] == '':
                missed_rows.append(i)
        missed_rows.append(len(current_status) + 1)

        current_row = missed_rows[0]
        missed_rows.pop(0)
        judge_done = False

        last_reset = time.time()

        print("Judge resetted")

    if judge_done:
        print("Finding next submission...")
        while True:
            if missed_rows != []:
                current_row = missed_rows[0]
                missed_rows.pop(0)
            else:
                current_row += 1
            
            if send_request(sheet.cell, current_row, 7).value == None:
                break

        print("Next submission found")
        
        judge_done = False

    row_data = send_request(sheet.row_values, current_row)
    if row_data == []:
        out_of_submission = True
        print("Waiting for new submission...")
        continue
    else:
        out_of_submission = False
    
    print(f"Submission #{current_row - 1}:")

    contestant = row_data[1]
    problem_id = row_data[3][0]
    problem_name = problems_data[problem_id]['name']
    extension = code_extension[row_data[4]]
    source_code = row_data[5]
    status = ''
    judge = ''
    if len(row_data) > 6:
        status = row_data[6]
        judge = row_data[7]

    submission_name = f"{str(current_row - 1).zfill(4)}[{contestant}][{problem_name}].{extension}"

    if status == '':
        send_request(sheet.update, [["Đang chờ...", judge_id]], f"G{current_row}:H{current_row}")

        with open("Submissions/" + submission_name, 'w', encoding = "utf8") as f:
            f.write(source_code)

        print("Change status to Waiting")
    elif judge == judge_id:
        if status == "Đang chờ...":
            if not os.path.exists("Submissions/" + submission_name):
                send_request(sheet.update_cell, current_row, 7, "Đang chấm...")
            
            print("Change status to Judging")
        elif status == 'Đang chấm...':
            if os.path.exists("Submissions/Logs/" + submission_name + ".log"):
                send_request(sheet.update_cell, current_row, 7, "Đã chấm")
                with open("Submissions/Logs/" + submission_name + ".log", 'r', encoding = 'utf8') as f:
                    total_points, max_execution_time, final_message, failed_test, tests_result = log_parser(f.read(), problems_data[problem_id])
                    formatted_log = format_log(total_points, max_execution_time, final_message, tests_result)
                    
                    send_request(sheet.update, [[total_points, max_execution_time, final_message, failed_test, formatted_log]], f"I{current_row}:M{current_row}")  
                
                judge_done = True

                print("Change status to Judged")
    else:
        judge_done = True

        print("Submission is judged by another judge")
