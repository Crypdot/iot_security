import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import tkinter as tk

load_dotenv()

# Parameters for the MQTT broker
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))
MQTT_TOPIC_PUMP_CONFIG = os.getenv("MQTT_TOPIC_PUMP_CONFIG")
MQTT_TOPIC_PUMP_COMMAND = os.getenv("MQTT_TOPIC_PUMP_COMMAND")

client = mqtt.Client()

"""
Default values for the different variables needed to command the pump.
"""
diffPressureRatio: float = 0.5
diffPressurePeriod: float = 8.0
diffPressureMinSpeed: int = 1300
diffPressureMaxSpeed: int = 1999
contPressureSpeed: int = 1500
pumpOperatingMode: int = 1

"""
Callback function called when the connection to the MQTT broker is established.
"""
def onConnect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT Broker at: {MQTT_BROKER_HOST}")
    else:
        print("Connection to MQTT Broker failed")

"""
Creates the main view presented to the user, containing the views for configuring both of the current modes we have available to us.
"""
class MainView(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.pumpRunning = False # Initially we assume the pump isn't running. This will be fetched from the MQTT
        self.root = root
        self.pack()
        self.createWidgets()

    def createWidgets(self):
        self.diffPressureButton = tk.Button(self, text="Differential Pressure Settings", command=self.showDiffPressureView)
        self.diffPressureButton.pack()

        self.contPressureButton = tk.Button(self, text="Continuous Pressure Settings", command=self.showContPressureView)
        self.contPressureButton.pack()

        self.togglePumpButton = tk.Button(self, text="Start Pump", command=self.togglePump)
        self.togglePumpButton.pack()

    def showDiffPressureView(self):
        self.pack_forget()
        DiffPressureView.pack()

    def showContPressureView(self):
        self.pack_forget()
        ContinuousPressureView.pack()

    def togglePump(self):
        if self.pumpRunning:
            self.pumpRunning = False
            self.togglePumpButton.config(text="Start Pump")
            print(f"STOPPING PUMP: Sending '0' to MQTT")
            client.publish(MQTT_TOPIC_PUMP_COMMAND, "0")
        else:
            self.pumpRunning = True
            self.togglePumpButton.config(text="Stop Pump")
            print(f"STARTING PUMP: Sending '1' to MQTT")
            client.publish(MQTT_TOPIC_PUMP_COMMAND, "1")

"""
Creates the view for the differential pressure configuration. Inputs are as follows:
- Rising duration: float
- Falling duration: float
- Minimum motor speed: int; between 1300 and 1999
- Maximum motor speed: int; between 1300 and 1999; cannot be below the minimum.

Failure to input the correct settings will result in an error.

Once the values have been validated, the configuration will then be published over MQTT in the following format:
MODE,CONTINUOUS_LEVEL,MIN,MAX,PERIOD,RATIO
"""
class DiffPressureView(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.createWidgets()
        self.pack_forget()

    def createWidgets(self):
        self.diffPressureViewLabel = tk.Label(self, text="Differential Pressure Settings")
        self.diffPressureViewLabel.pack()

        self.secondsXLabel = tk.Label(self, text="Rising Period")
        self.secondsXLabel.pack()
        self.secondsXEntry = tk.Entry(self)
        self.secondsXEntry.insert(0, diffPressurePeriod)
        self.secondsXEntry.pack()

        self.secondsYLabel = tk.Label(self, text="Falling Period")
        self.secondsYLabel.pack()
        self.secondsYEntry = tk.Entry(self)
        self.secondsYEntry.insert(0, diffPressurePeriod)
        self.secondsYEntry.pack()

        self.minSpeedLabel = tk.Label(self, text="Minimum Speed")
        self.minSpeedLabel.pack()
        self.minSpeedEntry = tk.Entry(self)
        self.minSpeedEntry.insert(0, diffPressureMinSpeed)
        self.minSpeedEntry.pack()

        self.maxSpeedLabel = tk.Label(self, text="Maximum Speed")
        self.maxSpeedLabel.pack()
        self.maxSpeedEntry = tk.Entry(self)
        self.maxSpeedEntry.insert(0, diffPressureMaxSpeed)
        self.maxSpeedEntry.pack()

        self.okButton = tk.Button(self, text="Confirm", command=self.onOKButtonClick)
        self.okButton.pack()

        self.backButton = tk.Button(self, text="Back", command=self.showMainView)
        self.backButton.pack()

        self.resultLabel = tk.Label(self, text="")
        self.resultLabel.pack()

    """
    Calculates the ratio between two given time periods.
    """
    def calculateRatio(self, x, y) -> float:
        return round(x/(x+y), 2)

    def onOKButtonClick(self):
        global diffPressureRatio, diffPressurePeriod, diffPressureMinSpeed, diffPressureMaxSpeed
        try:
            # Get values from the text inputs
            secondsRising = round(float(self.secondsXEntry.get()), 2)
            secondsFalling = round(float(self.secondsYEntry.get()), 2)
            minSpeed = int(self.minSpeedEntry.get())
            maxSpeed = int(self.maxSpeedEntry.get())

            # Check for negative values
            if secondsRising <= 0 or secondsFalling <= 0 or minSpeed <= 0 or maxSpeed <= 0:
                self.resultLabel.config(text="Error: Negative values are not allowed.")
                return

            # Check minimum speed and maximum speed limits
            if minSpeed < 1300:
                self.resultLabel.config(text="Error: Minimum speed should not be below 1300.")
                return

            if maxSpeed > 1999:
                self.resultLabel.config(text="Error: Maximum speed should not exceed 1999.")
                return

            if maxSpeed <= minSpeed:
                self.resultLabel.config(text="Maximum speed should not be set below the minimum.")
                return

            # If all checks pass, print the values
            print(f"Seconds Rising: {secondsRising}")
            print(f"Seconds Falling: {secondsFalling}")
            print(f"Minimum Speed: {minSpeed}")
            print(f"Maximum Speed: {maxSpeed}")

            #Save the OK values into global variables
            diffPressureRatio = self.calculateRatio(secondsRising, secondsFalling)
            diffPressureMinSpeed = minSpeed
            diffPressureMaxSpeed = maxSpeed
            diffPressurePeriod = secondsRising+secondsFalling
            pumpOperatingMode = 1

            # Publish the string to the MQTT server
            print(f"Config being sent to the Motor Controller!\n{pumpOperatingMode},{contPressureSpeed},{diffPressureMinSpeed},{diffPressureMaxSpeed},{diffPressurePeriod},{diffPressureRatio}\n")
            client.publish(MQTT_TOPIC_PUMP_CONFIG, f"{pumpOperatingMode},{contPressureSpeed},{diffPressureMinSpeed},{diffPressureMaxSpeed},{diffPressurePeriod},{diffPressureRatio}")
            
            self.resultLabel.config(text="Values successfully processed.")
        except ValueError:
            self.resultLabel.config(text="Error: Please enter valid values.")
        except Exception as e:
            print("An unexpected error occurred: " + str(e))

    def showMainView(self):
        self.pack_forget()
        MainView.pack()

"""
Creates the view for the continuous pressure configuration. Inputs are as follows:
- Desired motor speed: int; between 1300 and 1999

Currently, the purpose of the continuous pressure mode will be to simply maintain a specific speed indefinitely.
Future variables may be introduced if necessary.

Once the values have been validated, the configuration will then be published over MQTT in the following format:
MODE,CONTINUOUS_LEVEL,MIN,MAX,PERIOD,RATIO
"""
class ContinuousPressureView(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.createWidgets()
        self.pack_forget()

    def createWidgets(self):
        self.continuousPressureLabel = tk.Label(self, text="Continuous Pressure Settings")
        self.continuousPressureLabel.pack()

        self.continuousPressureEntry = tk.Entry(self)
        self.continuousPressureEntry.pack()

        self.okButton = tk.Button(self, text="Confirm", command=self.onOKButtonClick)
        self.okButton.pack()

        self.backButton = tk.Button(self, text="Back", command=self.showMainView)
        self.backButton.pack()

        self.resultLabel = tk.Label(self, text="")
        self.resultLabel.pack()

    def onOKButtonClick(self):
        global contPressureSpeed
        try:
            contPressureSpeed = int(self.continuousPressureEntry.get())
            if contPressureSpeed < 1300 or contPressureSpeed >= 1999:
                self.resultLabel.config(text="The value must be an integer between 1300 and 1999.")
                return
            
            pumpOperatingMode = 0
            print(f"Continuous Pressure: {contPressureSpeed}")
            
            print(f"Config being sent to the Motor Controller!\n{pumpOperatingMode},{contPressureSpeed},{diffPressureMinSpeed},{diffPressureMaxSpeed},{diffPressurePeriod},{diffPressureRatio}\n")
            client.publish(MQTT_TOPIC_PUMP_CONFIG, f"{pumpOperatingMode},{contPressureSpeed},{diffPressureMinSpeed},{diffPressureMaxSpeed},{diffPressurePeriod},{diffPressureRatio}")
            
            self.resultLabel.config(text="Values successfully processed.")
        except ValueError:
            self.resultLabel.config(text="Error: Please enter a valid integer value.")
        except Exception as e:
            print("An unexpected error occurred: " + str(e))

    def showMainView(self):
        self.pack_forget()
        MainView.pack()

"""
Closing Tkinter window calls this function.
Gracefully disconnect the MQTT client and close the Tkinter window.
"""
def onClosing():
    client.disconnect()
    root.quit()

if __name__ == "__main__":
    client.on_connect = onConnect
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

    # Create the main window
    root = tk.Tk()
    root.title("Beta Version for the Command Manager")

    # Bind closing function to the window closing
    root.protocol("WM_DELETE_WINDOW", onClosing)

    # Create instances of the views
    MainView = MainView(root)
    DiffPressureView = DiffPressureView(root)
    ContinuousPressureView = ContinuousPressureView(root)

    # Start the tkinter main loop
    root.mainloop()