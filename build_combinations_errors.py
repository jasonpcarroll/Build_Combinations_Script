from pathlib import Path
import re
import argparse
import os
from multiprocessing import Pool

# used for regex sub in order to compare lines without numbers that would
# otherwise make lines seem distinct
removal_str = "[1234567890 \t]"

# this is used to cut down on false positive error lines
error_str_blacklist = [
        "0 Error(s)",
        "pdFAIL",
        "/* data verify failed */"
    ]

def parse_errors_from_log(log_file_path):

    unique_error_lines = []
    unique_error_lines_with_removal = []

    error_str_with_removal: str = ""
    error_str_full: str = ""

    found_error_line = False

    with open(log_file_path, 'r') as log_file:
        for line in log_file:
            if not found_error_line:
                if re.search(r"\b" + "error" + r"\b" + "|fail", re.sub("[.]", "", line.lower())) and not any((str in line) for str in error_str_blacklist):
                    found_error_line = True
                    if re.sub(removal_str, '', line) not in unique_error_lines_with_removal:
                        unique_error_lines_with_removal.append(re.sub(removal_str, '', line))
                        unique_error_lines.append(line)
                    error_str_with_removal = error_str_with_removal + re.sub(removal_str, '', line)
                    error_str_full = error_str_full + line
            else:
                if re.search(r"\b" + "error" + r"\b" + "|fail", re.sub("[.]", "", line.lower())) and not any((str in line) for str in error_str_blacklist):
                    if re.sub(removal_str, '', line) not in unique_error_lines_with_removal:
                        unique_error_lines_with_removal.append(re.sub(removal_str, '', line))
                        unique_error_lines.append(line)
                error_str_with_removal = error_str_with_removal + re.sub(removal_str, '', line)
                error_str_full = error_str_full + line
            
    return error_str_with_removal, error_str_full, unique_error_lines

def parse_errors_for_board(board_directory, board_name_str, output_path="error_summaries"):

    unique_error_lines_board_dict = {}

    unique_error_logs_dict = {}
    error_log_files = Path(board_directory).iterdir()

    log_count = 0
    logs_with_error_count = 0

    for error_log in error_log_files:
        log_count += 1
        error_str_with_removals, error_str_full, unique_error_lines_log = parse_errors_from_log(error_log)

        if error_str_with_removals == "":
            continue

        logs_with_error_count += 1

        for unique_error_line in unique_error_lines_log:
            if re.sub(removal_str, '', unique_error_line) not in unique_error_lines_board_dict.keys():
                unique_error_lines_board_dict[re.sub(removal_str, '', unique_error_line)] = [unique_error_line, 1]
            else:
                unique_error_lines_board_dict[re.sub(removal_str, '', unique_error_line)][1] += 1

        if error_str_with_removals in unique_error_logs_dict.keys():
            unique_error_logs_dict[error_str_with_removals][2] += 1
        else:
            unique_error_logs_dict[error_str_with_removals] = [error_log.name, error_str_full, 1]

    # sort unique error lines by occurrence
    unique_error_lines_board_dict = {k: v for k, v in sorted(unique_error_lines_board_dict.items(), key=lambda item: item[1][1], reverse=True)}

    print(f'--------------------------------------------')
    print(f'Board Name: {board_name_str}')
    print(f'Number of logs: {log_count}')
    print(f'Number of error logs: {logs_with_error_count}')
    print(f"Number of unique error logs: {len(unique_error_logs_dict.keys())}")
    print(f"Number of unique error lines in logs: {len(unique_error_lines_board_dict)}")
    print(f'--------------------------------------------')

    if len(unique_error_logs_dict.keys()) != 0:

        output_path = Path(output_path, f"{board_name_str}_error_summary.txt")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as error_summary_file:

            error_summary_file.write(f'********************************************\n')
            error_summary_file.write(f'Summary for {board_name_str}\n')
            error_summary_file.write(f'********************************************\n\n')
 
            error_summary_file.write(f'Number of logs: {log_count}\n')
            error_summary_file.write(f'Number of error logs: {logs_with_error_count}\n')
            error_summary_file.write(f"Number of unique error lines in logs: {len(unique_error_lines_board_dict)}\n")
            error_summary_file.write(f"Number of unique error logs: {len(unique_error_logs_dict.keys())}\n\n")


            error_summary_file.write(f'********************************************\n')
            error_summary_file.write(f'Unique error lines across all logs ({len(unique_error_lines_board_dict)}). Sorted by number of occurrences.\n')
            error_summary_file.write(f'********************************************\n')
            error_num = 1
            for unique_error_line in unique_error_lines_board_dict.values():
                error_summary_file.write(f"{error_num}. Occurrences: {unique_error_line[1]} Line: {unique_error_line[0]}")
                error_num += 1
            error_summary_file.write(f'\n')

            error_summary_file.write(f'********************************************\n')
            error_summary_file.write(f'Unique error logs ({len(unique_error_logs_dict.keys())})\n')
            error_summary_file.write(f'********************************************\n')
            error_num = 1
            for value in unique_error_logs_dict.values():
                error_summary_file.write(f'--------------------------------------------\n')
                error_summary_file.write(f'Start of unique error log #{error_num}\n')
                error_summary_file.write(f"Log file: {value[0]}\n")
                error_summary_file.write(f"Number of logs like this one: {value[2]}\n")
                error_summary_file.write(f"Error excerpt:\n\n")
                error_summary_file.write(value[1])
                error_summary_file.write(f'End of unique error log #{error_num}\n')
                error_summary_file.write(f'--------------------------------------------\n')
                error_num += 1

def parse_build_combinations_errors(build_combinations_path, num_processes):
    vendor_dirs = Path(build_combinations_path).iterdir()
    board_tups = []

    for vendor_dir in vendor_dirs:
        board_tups += [(board_dir, board_dir.name) for board_dir in vendor_dir.iterdir()]
    pool = Pool(num_processes)
    pool.starmap(parse_errors_for_board, board_tups)

def main():
    parser = argparse.ArgumentParser(description='Build_Combinations error parser.')

    parser.add_argument('build_combinations_path',
                        type=str,
                        help='Path to Build_Combinations.')

    parser.add_argument('--output_path',
                        type=str,
                        required=False,
                        help='Path to directory where error files are written. By default they get written to \"error_summaries\"')

    parser.add_argument('-n',
                        '--num_processes',
                        type=int,
                        default=4,
                        required=False,
                        help='Number of processes to run in parallel')

    args = parser.parse_args()

    parse_build_combinations_errors(args.build_combinations_path, args.num_processes)

if __name__ == "__main__":
    main()