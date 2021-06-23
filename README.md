# Build_Combinations_Script

Pretty quick and dirty...

Usage is just:

python build_combinations_errors.py path_to_build_combinations_folder [--output_path]

For example:

python python build_combinations_errors.py archive/Build_Combinations

By default the logs go to "error_summaries," but you can specify where it goes with --ouput_path.

The script finds unique error lines among each board's logs and also unique error logs, where a unique error log is unique if, from the first error line that occurred to the end of the file, it is different to all error logs that were read before it (except for numbers - logs are compared with numbers removed). The output files give the unique error lines and then the unique logs.
