import subprocess
import sys
import os

"""
This script starts a new subprocess for each of the wanted scripts. The paths are defined and then executed using the Python interpreter currently running the script.
Each script's output is discarded (using /dev/null). These could be directed to a file for example, by giving the 'stdout' an open file. 

Each process ID is saved to a file. These are used by 'stop.py' to terminate the processes. 
"""
try:
    # Current directory, to find the scripts
    directory = os.path.dirname(os.path.abspath(__file__))

    # Defining the paths
    command_manager_ui = os.path.join(directory, "command-manager-ui.py")
    motor_controller = os.path.join(directory, "motor-controller.py")
    solo_display = os.path.join(directory, "solo-display.py")

    # Starting new processes. Output directed to /dev/null
    manager_process = subprocess.Popen([sys.executable, command_manager_ui], cwd=directory, stdout=subprocess.DEVNULL)
    controller_process = subprocess.Popen([sys.executable, motor_controller], cwd=directory, stdout=subprocess.DEVNULL)
    display_process = subprocess.Popen([sys.executable, solo_display], cwd=directory, stdout=subprocess.DEVNULL)

    # Writing process IDs to a file
    with open("pids.txt", "w") as file:
        file.write(f"{manager_process.pid}\n")
        file.write(f"{controller_process.pid}\n")
        file.write(f"{display_process.pid}\n")

except subprocess.CalledProcessError as e:
    print(f"Error: {e}")