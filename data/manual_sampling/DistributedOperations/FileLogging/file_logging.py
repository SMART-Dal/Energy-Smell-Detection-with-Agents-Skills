import time
import os

def log_time(n: int):
    file_name = "timer_log.txt"
    if os.path.exists(file_name):
        os.remove(file_name)
    with open(file_name, "a+") as f:
        for i in range(n):
            f.write(f"{i+1}: {time.time()}\n")


n = int(1e6)
log_time(n)

    