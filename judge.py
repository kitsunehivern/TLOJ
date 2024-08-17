import os
import time
import json
import gspread

with open("data.json", 'r', encoding = 'utf8') as f:
    data = json.load(f)

    sheet_id = data['sheet_id']
    contest_id = data['contest_id']

    problems_data = data['problems_data']

with open("config.json", 'r', encoding = 'utf8') as f:
    config = json.load(f)

    round_digits = config['round_digits']

    result_message = config['result_message']
    code_extension = config['code_extension']

    delay_time = config['delay_time']
    reset_time = config['reset_time']

with open("key.json", 'r') as f:
    key = json.load(f)

    judge_id = key['client_id']

print("Connecting to Google Sheets...")

client = gspread.service_account("key.json")
sheet = client.open_by_key(sheet_id).worksheet(f"{contest_id}")

print("Connected to Google Sheets")

def log_parser(log, problem_data):
    logs = log.split('\n')

    problem_name, language = logs[1].split('.')

    assert problem_name == problem_data['name'], "Problem name does not match"

    total_points = 0
    max_execution_time = 0
    final_message = result_message['AC']
    tests_result = []
    failed_test = 0
    if result_message['CE'] in log:
        failed_test = 1
        final_message = result_message['CE']
        message = result_message['CE']
        for i in range(3, len(logs) - 1):
            if logs[i] == "Dịch lỗi!":
                break

            if logs[i].split('.')[0] == problem_name:
                logs[i] = logs[i].replace(problem_name, 'main', 1)
            elif logs[i].split(' ')[0] == 'Error:' and language == 'pas': # Pascal, why?
                continue

            message += '\n' + logs[i]

        message = message[:10000] + "..." if len(message) > 10000 else message

        tests_result.append({'points': 0, 'execution_time': 0, 'message': message})
    else:
        total_points = round(float(logs[0].split(' ')[-1].replace(',', '.')), round_digits)

        i = 1
        while i < len(logs) and chr(0x2023) not in logs[i]:
            i += 1

        while i < len(logs):
            j = i + 1
            while j < len(logs) and chr(0x2023) not in logs[j]:
                j += 1
            j -= 1

            points = round(float(logs[i].split(' ')[-1].replace(',', '.')), round_digits)
            execution_time = 0
            message = result_message['AC']
            exit_code = 0
            for k in range(i, j + 1):
                words = logs[k].split(' ')

                for message_code in ['WA', 'RE', 'TLE', 'NF']:
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
            
            if message != result_message['AC'] and failed_test == 0:
                failed_test = len(tests_result) + 1
                final_message = message
            
            if message == result_message['RE']:
                message += f' (exit code: {exit_code})'

            tests_result.append({'points': points, 'execution_time': execution_time, 'message': message})

            i = j + 1

    total_points = round(total_points, round_digits)

    if final_message == result_message['AC']:
        failed_test = len(tests_result)

    return total_points, max_execution_time, final_message, failed_test, tests_result

def format_log(total_points, max_execution_time, final_message, tests_result):
    log = f"Tổng: [{f"%.{round_digits}f" % total_points} điểm, {max_execution_time} ms] {final_message}"
    for i in range(len(tests_result)):
        log += f"\n#{i + 1}: [{f"%.{round_digits}f" % tests_result[i]['points']} điểm, {tests_result[i]['execution_time']} ms] {tests_result[i]['message']}"

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
submission_status = ""
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
        submission_status = "Queuing..."

    row_data = send_request(sheet.row_values, current_row)
    if row_data == []:
        out_of_submission = True
        print("Waiting for new submission...")
        continue
    else:
        out_of_submission = False
    
    print(f"Submission #{current_row - 1}:", submission_status)

    contestant = row_data[1]
    problem_id = row_data[2][:row_data[2].find('.')]
    problem_name = problems_data[problem_id]['name']
    extension = code_extension[row_data[3]]
    source_code = row_data[4]
    status = ''
    judge = ''
    if len(row_data) >= 7:
        status = row_data[5]
        judge = row_data[6]

    submission_name = f"{str(current_row - 1).zfill(4)}[{contestant}][{problem_name}].{extension}"

    if status == '':
        send_request(sheet.update, [["Đang chờ...", judge_id]], f"F{current_row}:G{current_row}")

        with open("Submissions/" + submission_name, 'w', encoding = 'utf8') as f:
            f.write(source_code)

        submission_status = "Waiting..."
        print("Change status to Waiting")
    elif judge == judge_id:
        if status == "Đang chờ...":
            if not os.path.exists("Submissions/" + submission_name):
                send_request(sheet.update_cell, current_row, 6, "Đang chấm...")

                submission_status = "Judging..."
                print("Change status to Judging")
        elif status == "Đang chấm...":
            if os.path.exists("Submissions/Logs/" + submission_name + ".log"):
                send_request(sheet.update_cell, current_row, 6, "Đã chấm")
                with open("Submissions/Logs/" + submission_name + ".log", 'r', encoding = 'utf8') as f:
                    total_points, max_execution_time, final_message, failed_test, tests_result = log_parser(f.read(), problems_data[problem_id])
                    formatted_log = format_log(total_points, max_execution_time, final_message, tests_result)
                    
                    send_request(sheet.update, [[f"%.{round_digits}f" % total_points, max_execution_time, final_message, failed_test, formatted_log]], f"H{current_row}:L{current_row}")  
                
                judge_done = True

                submission_status = "Judged"
                print("Change status to Judged")
    else:
        judge_done = True

        submission_status = "Skipped"
        print("Submission is judged by another judge")
