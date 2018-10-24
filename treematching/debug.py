trace = False
import sys

def log_on():
    global trace
    trace = True

def log_off():
    global trace
    trace = False

def log(*t):
    if trace:
       print(*t, flush=True, file=sys.stdout)
