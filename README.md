# Hot-Spot Pi HAT: Advanced PCB Heat Detection and Thermal Visualization

This project is a Raspberry Pi based device that watches a circuit board for overheating. It uses a small thermal sensor and a camera to keep checking the temperature of a PCB. If any part of the board gets too hot, the device takes a photo, marks the hot spot on that photo, sounds a buzzer, and can cut off the power to prevent damage.

It was built as a low-cost alternative to expensive thermal imaging equipment, mainly to catch overheating components early, before they cause real damage.

---

## What You Need (Hardware)

- Raspberry Pi 3 Model A+ (or similar)
- AMG8833 thermal camera sensor (8x8 pixels)
- Raspberry Pi Camera Module Rev 1.3
- A buzzer
- An NPN transistor and a 10k ohm resistor (for the buzzer circuit)
- A single channel relay module
- Jumper wires
- A microSD card with Raspberry Pi OS installed

The full wiring diagram is included in the `schematic` folder of this repository. Connect the AMG8833 sensor using the I2C pins, connect the camera to the CSI port, and wire the buzzer and relay to the GPIO pins as shown in the diagram.

---

## How to Download This Project

1. Open the terminal on your Raspberry Pi.
2. Make sure Git is installed. If not, install it using:

```
sudo apt install git -y
```

3. Download (clone) this project using:

```
git clone https://github.com/Prem2k03/Thermal-based-Hot-Spot-identification
```

4. Move into the project folder:

```
cd hotspot-pi-hat
```

That's it, you now have all the project files on your Raspberry Pi.

If you don't want to use Git, you can also just click the green "Code" button on the GitHub page and choose "Download ZIP", then extract it on your Raspberry Pi.

---

## How to Set Up the Raspberry Pi

Before running the code, a few things need to be set up on the Raspberry Pi.

**Step 1: Enable I2C**

The AMG8833 sensor talks to the Raspberry Pi using I2C, so this needs to be turned on first.

```
sudo raspi-config
```

Go to "Interface Options", then select "I2C", and choose "Yes" to enable it. Then restart the Raspberry Pi.

**Step 2: Check if the sensor is detected**

```
sudo apt install i2c-tools -y
i2cdetect -y 1
```

If everything is connected properly, you should see a number like 68 or 69 appear in the table. This confirms the AMG8833 sensor is being detected.

**Step 3: Install Python and required libraries**

Most Raspberry Pi OS versions already come with Python 3 installed. You can check this with:

```
python3 --version
```

Now install all the libraries the project needs by running this single command:

```
pip install opencv-python numpy adafruit-blinka adafruit-circuitpython-amg88xx pillow picamera2 matplotlib RPi.GPIO
```

This installs everything needed for the camera, the thermal sensor, image processing, graphing, and GPIO control.

---

## How to Use the Device

Once everything is installed and wired up correctly, you can run the main script:

```
python3 Hotspot_pi_hat.py
```

When the script starts, it will continuously read the temperature data from the AMG8833 sensor and print it on the screen. This is the live monitoring stage, the device is simply watching the board for any signs of overheating.

The moment any part of the sensor's view crosses the temperature threshold, the live monitoring stops automatically and the following happens, one after another:

- The last thermal reading is saved as a CSV file, so you have a record of the exact temperatures at the time of the fault.
- The camera takes a picture of the PCB.
- The software looks at which part of the thermal data was overheating, and draws a red box on the captured photo to show exactly where the hot spot is.
- A few graphs are generated automatically, a smoother heatmap image, a 3D temperature graph, a line graph showing temperature of every pixel, and a histogram showing how many pixels were at each temperature.
- The buzzer starts beeping to alert you, and if you have the relay wired to your power source, it can be used to cut off power automatically.

To stop the buzzer, simply press the Enter key in the terminal. This will stop the alert and clean up the GPIO pins safely before the program closes.

All the saved files (CSV data, captured images, processed images, and graphs) will be stored in folders inside the project directory, so you can go back and look at them anytime, even after the program has closed.

---

## Adjusting the Temperature Threshold

If you want the device to be more or less sensitive to heat, you can open the `Hotspot_pi_hat.py` file in any text editor and change this line near the top:

```
TEMP_THRESHOLD = 20.0
```

Change the number to whatever temperature (in Celsius) you want the device to react to. Lower numbers make it more sensitive, higher numbers make it less sensitive.

---

## Testing the Device Safely

If you don't want to test this directly on a real circuit board, you can build a simple test board instead. This project also includes a small 3x3 grid of resistors, controlled by 6 switches, three for rows and three for columns. By turning on one row switch and one column switch together, you can heat up just one resistor at a time using a 12 volt power supply. This is a safe way to create a controlled hot spot and check if the device detects it correctly. Details and the circuit diagram for this test setup are in the `test-rig` folder.

---

## Notes

- This project is built and tested on Raspberry Pi OS (Legacy 32-bit).
- Make sure the camera ribbon cable is connected properly before running the script, otherwise the camera initialization will fail.
- If the script gives an error about the camera or sensor not being found, double check your wiring and make sure I2C is enabled.

---

## Author

Premkumar S
M.Sc. Electronics and Communication Systems
Sri Krishna Arts and Science College, Coimbatore

Project Guide: Dr. S. Devendiran, Assistant Professor, Department of ECS
