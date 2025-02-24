import subprocess
import sys

subprocess.check_call(
    ["apksigner", "verify", "--verbose", "--print-certs", sys.argv[1]],
    shell=True,
)
