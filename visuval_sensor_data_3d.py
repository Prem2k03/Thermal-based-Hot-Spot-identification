import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import csv

# Load 8x8 CSV data
csv_filename = 'D:/Documents/PG-REPORT/LinkedIn Pi-Hat Project/thermal_output.csv'
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

# Plot 3D Surface
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")
ax.plot_surface(X, Y, Z, cmap="jet")

# Labels and Title
ax.set_xlabel("X Axis (Grid Columns)")
ax.set_ylabel("Y Axis (Grid Rows)")
ax.set_zlabel("Temperature (°C)")
ax.set_title("3D Thermal Data Visualization")

plt.show()
