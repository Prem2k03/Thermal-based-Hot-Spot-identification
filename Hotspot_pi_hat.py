import os
import cv2
import numpy as np
import board
import busio
import adafruit_amg88xx
import csv
import time
import threading
from PIL import Image
from picamera2 import Picamera2
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import RPi.GPIO as GPIO

# ---------------------------------------------------------------------------
# GPIO Setup
# ---------------------------------------------------------------------------
GPIO.setmode(GPIO.BCM)        # Use Broadcom pin numbering
GPIO.setup(4, GPIO.OUT)       # Set GPIO 4 as an output
GPIO.output(4, GPIO.LOW)      # Set GPIO 4 LOW initially

# ---------------------------------------------------------------------------
# Constants & Paths
# ---------------------------------------------------------------------------
TEMP_THRESHOLD = 20.0  # Overheat detection threshold
SENSOR_DATA_PATH = "sensor_data"
IMG_PATH = "img"
OUTPUT_PATH = "output"

# Ensure directories exist
os.makedirs(SENSOR_DATA_PATH, exist_ok=True)
os.makedirs(IMG_PATH, exist_ok=True)
os.makedirs(OUTPUT_PATH, exist_ok=True)

# ---------------------------------------------------------------------------
# Initialize AMG8833 Thermal Sensor
# ---------------------------------------------------------------------------
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_amg88xx.AMG88XX(i2c)

# ---------------------------------------------------------------------------
# Initialize Picamera2
# ---------------------------------------------------------------------------
picam2 = Picamera2()
camera_config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(camera_config)
picam2.start()

GRID_SIZE = 8  # 8x8 sensor grid
FRAME_WIDTH, FRAME_HEIGHT = 640, 480  # Camera image size
GRID_X, GRID_Y = FRAME_WIDTH // GRID_SIZE, FRAME_HEIGHT // GRID_SIZE  # Mapping to image

time.sleep(2)  # Allow sensors to stabilize

# ---------------------------------------------------------------------------
# Live Thermal Monitoring Loop
# ---------------------------------------------------------------------------
overheat_detected = False  # Flag to track overheat

while not overheat_detected:
    # Capture live thermal data
    thermal_data = np.array(sensor.pixels)

    # Display thermal output in console (Optional)
    print("Thermal Data:")
    print(thermal_data)

    # Check for overheated cells
    hot_spots = np.argwhere(thermal_data > TEMP_THRESHOLD)

    if hot_spots.size > 0:
        print("\nOverheat detected! Stopping live feed...")
        overheat_detected = True
        break  # Exit the live feed loop

    time.sleep(1)  # Slow down the loop for better efficiency

# ---------------------------------------------------------------------------
# Step 1: Save Last Thermal Data to CSV
# ---------------------------------------------------------------------------
thermal_csv_path = os.path.join(SENSOR_DATA_PATH, "thermal_output.csv")
with open(thermal_csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(thermal_data)
print(f"\nThermal data saved at: {thermal_csv_path}")

# ---------------------------------------------------------------------------
# Step 2: Capture Camera Image (with a quick LED/flash blink via GPIO 4)
# ---------------------------------------------------------------------------
GPIO.output(4, GPIO.HIGH)
time.sleep(0.2)
GPIO.output(4, GPIO.LOW)
time.sleep(0.2)
GPIO.output(4, GPIO.HIGH)
time.sleep(0.2)
GPIO.output(4, GPIO.LOW)

img_path = os.path.join(IMG_PATH, "captured_image.jpg")
picam2.capture_file(img_path)
print(f"\nImage captured and saved at: {img_path}")

# ---------------------------------------------------------------------------
# Step 3: Process AMG8833 Data & Overlay Bounding Boxes
# ---------------------------------------------------------------------------
camera_image = cv2.imread(img_path)
thermal_data_interpolated = cv2.resize(
    thermal_data, (80, 80), interpolation=cv2.INTER_LINEAR
)

# Find overheated positions
_, labeled = cv2.connectedComponents(
    (thermal_data > TEMP_THRESHOLD).astype(np.uint8)
)
num_labels = np.max(labeled)

for label in range(1, num_labels + 1):
    positions = np.argwhere(labeled == label)
    y_min, x_min = np.min(positions, axis=0)
    y_max, x_max = np.max(positions, axis=0)

    # Convert to pixel coordinates
    top_left = (int(x_min * GRID_X), int(y_min * GRID_Y))
    bottom_right = (int((x_max + 1) * GRID_X), int((y_max + 1) * GRID_Y))

    # Draw bounding box
    cv2.rectangle(camera_image, top_left, bottom_right, (0, 0, 255), 2)

# ---------------------------------------------------------------------------
# Step 4: Save Final Processed Image
# ---------------------------------------------------------------------------
output_img_path = os.path.join(OUTPUT_PATH, "output_image.jpg")
cv2.imwrite(output_img_path, camera_image)
print(f"\nProcessed image saved at: {output_img_path}")

# ---------------------------------------------------------------------------
# Step 5: Visualize in Matplotlib (Raw / Interpolated / Overlayed)
# ---------------------------------------------------------------------------
fig, axs = plt.subplots(1, 3, figsize=(15, 5))

# Display Raw AMG8833 sensor data
axs[0].imshow(thermal_data, cmap='hot', interpolation='nearest')
axs[0].set_title("Raw AMG8833 Sensor Data (8x8)")
axs[0].axis('off')

# Display Bilinear Interpolated AMG8833 (8x8 to 80x80)
axs[1].imshow(thermal_data_interpolated, cmap='hot', interpolation='nearest')
axs[1].set_title("Bilinear Interpolated AMG8833 (8x8-80x80)")
axs[1].axis('off')

# Display Camera Image with Bounding Boxes
camera_image_rgb = cv2.cvtColor(camera_image, cv2.COLOR_BGR2RGB)  # Convert to RGB for Matplotlib
axs[2].imshow(camera_image_rgb)
axs[2].set_title("Rectangle Overlayed Captured Image")
axs[2].axis('off')

plt.tight_layout()
plt.show()

# ---------------------------------------------------------------------------
# Load 8x8 CSV data (reload from saved CSV for the 3D / pixel plots below)
# ---------------------------------------------------------------------------
csv_filename = os.path.join(SENSOR_DATA_PATH, "thermal_output.csv")
thermal_data = []
with open(csv_filename, mode="r") as file:
    reader = csv.reader(file)
    for row in reader:
        thermal_data.append([float(value) for value in row])

# Convert to NumPy array
thermal_data = np.array(thermal_data)

# Create X, Y coordinates
x = np.arange(8)
y = np.arange(8)
X, Y = np.meshgrid(x, y)
Z = thermal_data  # Temperature values

# ---------------------------------------------------------------------------
# Plot 3D Surface
# ---------------------------------------------------------------------------
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")
ax.plot_surface(X, Y, Z, cmap="jet")

ax.set_xlabel("X Axis (Grid Columns)")
ax.set_ylabel("Y Axis (Grid Rows)")
ax.set_zlabel("Temperature (°C)")
ax.set_title("3D Thermal Data Visualization")
plt.show()

# ---------------------------------------------------------------------------
# Step 6: Generate Histogram for Temperature Distribution
# ---------------------------------------------------------------------------
graph_output_path = "/home/prem/project/graph"
os.makedirs(graph_output_path, exist_ok=True)  # Ensure directory exists

# Flatten 8x8 matrix to 1D array
temperature_values = thermal_data.flatten()

# Create histogram
plt.figure(figsize=(8, 5))
plt.hist(temperature_values, bins=20, color='blue', edgecolor='black', alpha=0.7)
plt.xlabel("Temperature (°C)")
plt.ylabel("Number of Pixels")
plt.title("AMG8833 Sensor Temperature Distribution")

# Save the graph
graph_image_path = os.path.join(graph_output_path, "temperature_distribution.jpg")
plt.savefig(graph_image_path)
graph_output = Image.open(graph_image_path)
plt.close()
print(f"\nGraph saved at: {graph_image_path}")

# ---------------------------------------------------------------------------
# Step 7: Generate Line Graph for Each Pixel's Temperature
# ---------------------------------------------------------------------------
line_chart_output_path = os.path.join(graph_output_path, "pixel_temperature_line_chart.jpg")

# X-axis: Pixel indices (1 to 64)
pixel_indices = np.arange(0, 64)

# Y-axis: Temperature values
pixel_temperatures = thermal_data.flatten()

# Create line graph
plt.figure(figsize=(10, 5))
plt.plot(
    pixel_indices, pixel_temperatures,
    marker='o', linestyle='-', color='blue',
    markersize=5, label="Temperature"
)

# Graph Labels
plt.xlabel("Pixel Number (1-64)")
plt.ylabel("Temperature (°C)")
plt.title("Temperature of Each AMG8833 Sensor Pixel")
plt.xticks(ticks=np.arange(1, 65, step=4))  # Show labels every 4 pixels for readability
plt.grid(True, linestyle='--', alpha=0.6)   # Add a grid for better readability
plt.legend()

# Save the line graph
plt.savefig(line_chart_output_path)
line_chart_output = Image.open(line_chart_output_path)
plt.close()
print(f"\nLine graph saved at: {line_chart_output_path}")

# Display saved graphs
plt.imshow(line_chart_output)
plt.axis('off')
plt.show()

plt.imshow(graph_output)
plt.axis('off')
plt.show()

# ---------------------------------------------------------------------------
# Buzzer / LED alert thread + quit listener
# ---------------------------------------------------------------------------
running = True  # Flag to control the alert loop


def toggle_led():
    """Blink GPIO 4 (buzzer/LED) repeatedly until 'running' is set to False."""
    while running:
        GPIO.output(4, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(4, GPIO.LOW)
        time.sleep(0.2)
        GPIO.output(4, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(4, GPIO.LOW)
        time.sleep(1)


def listen_for_quit():
    """Block until the user presses Enter, then stop the alert loop."""
    global running
    input("Press 'Enter' to quit.\n")
    running = False


def buzzer():
    """Start the alert thread and wait for the user to quit."""
    try:
        led_thread = threading.Thread(target=toggle_led)
        led_thread.start()
        listen_for_quit()
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()  # Clean up GPIO settings


buzzer()

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
picam2.stop()
cv2.destroyAllWindows()
