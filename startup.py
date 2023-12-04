import subprocess
from dotenv import load_dotenv
import sys
import os
import requests

from stop import stopProcesses

FILEPATH = "pids.txt"

"""
Checks that the configuration file exists. 
TODO: functionality to create and initialize .env file. 
"""
def checkEnv():
    if os.path.exists(".env"):
        load_dotenv()
    else:
        raise FileNotFoundError(".env does not exist.")

"""
Starts processes based on a list of script-argument pairs. Scripts are executed using Python interpreter currently running the script. 
Outputs are discarded. 
Each process ID is saved to a file. These are used by 'stop.py' to terminate the processes. 

Example input:
processes = [
    ("script1.py", ["arg1"]),
    ("/directory/script2.py", ["arg3", "arg4"]),
]

Script paths are relative to current directory. 
"""
def startProcesses(processes: list):
    try:
        # Current directory, to find the scripts
        directory = os.path.dirname(os.path.abspath(__file__))

        with open(FILEPATH, "w") as file:
            for script, arguments in processes:
                command = [sys.executable, script] + arguments
                process = subprocess.Popen(command, cwd=directory, stdout=subprocess.DEVNULL)
                file.write(f"{process.pid}\n")

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

"""
HTTP request to initiate the TPM authentication. 
WIP. 
"""
def sendHttpRequest():
    url = os.getenv("HTTP_HOST")

    try:
        response = requests.get(url)
    except Exception as e:
        print("Error")

    if response.status_code == 201:
        print("HTTP request successful.")
    else:
        print(f"Unsuccessful, response: {response}")

if __name__ == "__main__":

    processes = [
        ("commandManagerUi.py", []),
        ("motorController.py", []),
        ("displayManager.py", [])
    ]

    try:
        if os.path.exists(FILEPATH):
            print("Scripts already running. Restarting...")
            stopProcesses(FILEPATH)

        checkEnv()
        startProcesses(processes)
        sendHttpRequest()
    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"Error: {e}")