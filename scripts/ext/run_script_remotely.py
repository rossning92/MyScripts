import argparse
import os

from utils.remoteshell import run_bash_script_in_remote_shell

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=str, nargs="?", default=None)
    parser.add_argument(
        "-b", "--send-prev-job-to-background", default=False, action="store_true"
    )
    args = parser.parse_args()

    if args.file:
        script_path = args.file
    else:
        script_path = os.environ["SCRIPT"]

    run_bash_script_in_remote_shell(
        script_path, send_prev_job_to_background=args.send_prev_job_to_background
    )
