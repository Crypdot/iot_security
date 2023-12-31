import psutil
import os

"""
Script used to terminate all the processes listed in 'pids.txt'. 
Removes 'pids.txt' after completion. Does nothing if 'pids.txt' does not exist. 
"""
FILEPATH = "pids.txt"
def stopProcesses(filepath):
    print("Stopping processes...")
    with open(FILEPATH, "r") as file:
        for pid in file.readlines():
            try:
                process = psutil.Process(int(pid))
                process.terminate()
            except psutil.NoSuchProcess:
                print(f"Process with PID {pid} not found.")
            except Exception as e:
                print(f"Error terminating process {pid}: {e}")
    os.remove(FILEPATH)

if __name__ == "__main__":
    if os.path.exists(FILEPATH):
        stopProcesses(FILEPATH)