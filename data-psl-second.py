import serial
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# --- USER SETTINGS ---
PORT = "COM8"  # Change this to your correct COM port
BAUD = 115200  # Must match Serial.begin() in Arduino
MAX_POINTS = 100  # Number of points shown on graph at once

# --- Initialize Serial ---
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # give Arduino time to reset

# --- Data buffers ---
timestamps = []
forces = []

# --- Plot setup ---
plt.style.use("seaborn-v0_8-darkgrid")
fig, ax = plt.subplots()
(line,) = ax.plot([], [], lw=2, color="royalblue")
ax.set_title("Real-Time FSR406 Pressure Monitoring")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Pressure (N)")
ax.set_ylim(0, 12)  # adjust based on your force range
ax.set_xlim(0, MAX_POINTS)
plt.tight_layout()

start_time = time.time()


def update(frame):
    global timestamps, forces

    line_bytes = ser.readline().decode("utf-8").strip()
    if not line_bytes:
        return (line,)

    try:
        force = float(line_bytes)
    except ValueError:
        # skip invalid lines
        return (line,)

    # Get elapsed time since start
    t = time.time() - start_time

    # Append new data
    timestamps.append(t)
    forces.append(force)

    # Keep only the last MAX_POINTS
    timestamps = timestamps[-MAX_POINTS:]
    forces = forces[-MAX_POINTS:]

    # Update line data
    line.set_data(timestamps, forces)

    # Update axis limits dynamically
    ax.set_xlim(max(0, timestamps[0]), timestamps[-1] + 1)
    ax.set_ylim(0, max(10, max(forces) * 1.2))

    return (line,)


# --- Animate plot ---
ani = FuncAnimation(fig, update, interval=200, blit=True)

print("✅ Connected to Arduino Nano ESP32")
print("📊 Visualizing FSR406 force data in real time...")
print("Press Ctrl+C in this window to stop.")

try:
    plt.show()
except KeyboardInterrupt:
    print("\n🛑 Stopped by user.")
finally:
    ser.close()
    print("🔌 Serial connection closed.")
