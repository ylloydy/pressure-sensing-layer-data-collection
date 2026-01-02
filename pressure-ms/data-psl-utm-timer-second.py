import serial
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import csv
from datetime import datetime

from mysql_logger import create_connection, create_table, insert_force

# ---- USER SETTINGS ----
RUN_TIME_SECONDS = 20
SAMPLING_INTERVAL_MS = 100  # match Arduino delay(100) → 10 Hz

# ---- SERIAL SETUP ----
PORT = "COM8"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=0.001)
time.sleep(1)  # minimal stabilization time
ser.reset_input_buffer()  # prevent 5-second delay effect

# ---- MYSQL SETUP ----
conn = create_connection()
if conn:
    create_table(conn)
else:
    print("WARNING: MySQL NOT connected. Data will NOT be saved.")

# ---- DATA LISTS ----
forces = []
timestamps = []

plt.style.use("ggplot")
fig, ax = plt.subplots(figsize=(10, 5))
(line,) = ax.plot([], [], linewidth=2)
ax.set_title("Real-Time FSR406 Force Data (10 Hz)")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Force (N)")
ax.set_xlim(0, 10)
ax.set_ylim(0, 20)

start_time = time.time()


# -------------------------------------------------------
# SAVE CSV + IMAGE
# -------------------------------------------------------
def save_csv_and_image():
    if len(forces) == 0:
        print("No data recorded. Skipping export.")
        return

    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_filename = f"force_data_{timestamp_str}.csv"
    png_filename = f"force_graph_{timestamp_str}.png"

    # Save CSV
    with open(csv_filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp_seconds", "force_value"])
        for t, f in zip(timestamps, forces):
            writer.writerow([t, f])

    # Save static graph
    fig.savefig(png_filename, dpi=300)

    print(f"\n✔ CSV saved: {csv_filename}")
    print(f"✔ Graph saved: {png_filename}")


def stop_everything():
    print("\n⛔ Experiment finished — saving data...")
    save_csv_and_image()

    if conn:
        conn.close()
    ser.close()
    plt.close(fig)


def on_close(event):
    print("\nWindow closed manually — exporting data...")
    stop_everything()


fig.canvas.mpl_connect("close_event", on_close)


# -------------------------------------------------------
# REAL-TIME UPDATE (MATCHED TO 10 Hz)
# -------------------------------------------------------
def update(frame):
    current_time = time.time() - start_time

    # ---- Auto-stop ----
    if current_time >= RUN_TIME_SECONDS:
        stop_everything()
        return

    # ---- Read one serial line ----
    try:
        raw = ser.readline().decode().strip()
        if raw:
            value = float(raw)

            timestamps.append(current_time)
            forces.append(value)

            if conn:
                insert_force(conn, value)
    except:
        pass

    # ---- Update plot ----
    if len(forces) > 0:
        line.set_data(timestamps, forces)
        ax.set_xlim(max(0, timestamps[-1] - 10), timestamps[-1] + 1)
        ax.set_ylim(min(forces) - 1, max(forces) + 3)

    return (line,)


ani = animation.FuncAnimation(fig, update, interval=SAMPLING_INTERVAL_MS)

plt.show()
