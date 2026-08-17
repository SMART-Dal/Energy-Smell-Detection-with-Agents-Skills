import time
import os

def log_time(n: int):
    file_name = "log_timer.txt"
    if os.path.exists(file_name):
        os.remove(file_name)
    texts = []
    for i in range(n):
        texts.append(f"{i+1}: {time.time()}\n")
    text_to_write = "".join(texts)
    with open(file_name, "a+") as f:
        f.write(text_to_write)


n = int(1e6)
log_time(n)

    