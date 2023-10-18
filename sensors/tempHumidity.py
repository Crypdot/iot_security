import serial
import time

arduino_port = "/dev/ttyACM0"  # Make sure this COM port is *your* Arduino's port!

ser = serial.Serial(arduino_port, 9600, timeout=1)

try:
    while True:
        user_input = input("Enter 't' for temperature or 'h' for humidity: ")
        if user_input == 't' or user_input == 'h':
            ser.write(user_input.encode())  # Send 't' or 'h' to Arduino
            data = ser.readline().decode().strip()  # Read the response from the Arduino
            print(f"Received data: {data}")
        else:
            print("Invalid input. Enter 't' or 'h'.")

except KeyboardInterrupt:
    ser.close()  # Here we close the serial connection when done
