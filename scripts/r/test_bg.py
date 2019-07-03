import subprocess
import sys
import subprocess
import threading


def myrun(cmd):
    def print_output(ps):
        while True:
            line = ps.stdout.readline()
            sys.stdout.buffer.write(line) # stdout is thread-safe
            sys.stdout.flush()
            if line == '' and ps.poll() is not None:
                break

    ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    t = threading.Thread(target=print_output, args=(ps,))
    t.start()


myrun('ping -t 127.0.0.1')
myrun('ping -t localhost')
# subprocess.Popen('ping -t localhost')
