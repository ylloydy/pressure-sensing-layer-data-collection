import serial
import time
import os
import csv
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from mysql_logger import create_connection, create_table, insert_force

# =======================================================
# USER SETTINGS
# =======================================================
RUN_TIME_SECONDS = 20
SAMPLING_INTERVAL_MS = 100  # 10 Hz (matches Arduino delay)

PORT = "COM8"
BAUD = 115200

# =======================================================
# SAVE DIRECTORY SETUP
# =======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "pressure-ms")

# Create directory if it does not exist
os.makedirs(SAVE_DIR, exist_ok=True)

# =======================================================
# SERIAL SETUP
# =======================================================
ser = serial.Serial(PORT, BAUD, timeout=0.001)
time.sleep(1)
ser.reset_input_buffer()

# =======================================================
# MYSQL SETUP
# =======================================================
conn = create_connection()
if conn:
    create_table(conn)
else:
    print("⚠ WARNING: MySQL NOT connected. Data will NOT be saved to database.")

# =======================================================
# DATA STORAGE
# =======================================================
forces = []
timestamps = []

# =======================================================
# PLOT SETUP
# =======================================================
plt.style.use("ggplot")
fig, ax = plt.subplots(figsize=(10, 5))

(line,) = ax.plot([], [], linewidth=2)
ax.set_title("Real-Time FSR406 Force Data (10 Hz)")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Force (N)")
ax.set_xlim(0, 10)
ax.set_ylim(0, 20)

start_time = time.time()


# =======================================================
# SAVE CSV + IMAGE
# =======================================================
def save_csv_and_image():
    if not forces:
        print("No data recorded. Skipping export.")
        return

    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    csv_path = os.path.join(SAVE_DIR, f"force_data_{timestamp_str}.csv")
    png_path = os.path.join(SAVE_DIR, f"force_graph_{timestamp_str}.png")

    # ---- Save CSV ----
    with open(csv_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp_seconds", "force_value_N"])
        for t, f in zip(timestamps, forces):
            writer.writerow([t, f])

    # ---- Save Graph ----
    fig.savefig(png_path, dpi=300)

    print("\n✔ CSV saved:", csv_path)
    print("✔ Graph saved:", png_path)


# =======================================================
# CLEAN SHUTDOWN
# =======================================================
def stop_everything():
    print("\n⛔ Experiment finished — saving data...")
    save_csv_and_image()

    if conn:
        conn.close()

    if ser.is_open:
        ser.close()

    plt.close(fig)


def on_close(event):
    print("\nWindow closed manually — exporting data...")
    stop_everything()


fig.canvas.mpl_connect("close_event", on_close)


# =======================================================
# REAL-TIME UPDATE LOOP (10 Hz)
# =======================================================
def update(frame):
    current_time = time.time() - start_time

    # ---- Auto stop ----
    if current_time >= RUN_TIME_SECONDS:
        stop_everything()
        return

    try:
        raw = ser.readline().decode().strip()
        if raw:
            force_value = float(raw)

            timestamps.append(current_time)
            forces.append(force_value)

            if conn:
                insert_force(conn, force_value)

    except ValueError:
        pass
    except Exception as e:
        print("Serial error:", e)

    # ---- Update plot ----
    if forces:
        line.set_data(timestamps, forces)
        ax.set_xlim(max(0, timestamps[-1] - 10), timestamps[-1] + 1)
        ax.set_ylim(min(forces) - 1, max(forces) + 3)

    return (line,)


# =======================================================
# START ANIMATION
# =======================================================
ani = animation.FuncAnimation(
    fig, update, interval=SAMPLING_INTERVAL_MS, cache_frame_data=False
)

plt.show()
