import serial
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import csv
from datetime import datetime

from mysql_logger import create_connection, create_table, insert_force


# ---- SERIAL SETUP ----
PORT = "COM8"
BAUD = 115200  ## 230400
ser = serial.Serial(PORT, BAUD, timeout=0.001)
time.sleep(1)


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
ax.set_title("Real-Time FSR406 Force Data")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Force (N)")
ax.set_xlim(0, 10)
ax.set_ylim(0, 20)

start_time = time.time()


# -------------------------------------------------------
#    AUTO-SAVE CSV + FULL GRAPH SNAPSHOT ON CLOSE
# -------------------------------------------------------


def save_csv_and_image():
    """Exports to CSV and saves a full-range graph snapshot (0 → last time)."""
    if len(forces) == 0:
        print("No data recorded. Skipping export.")
        return

    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_filename = f"force_data_{timestamp_str}.csv"
    png_filename = f"force_graph_{timestamp_str}.png"

    # ---- SAVE CSV ----
    with open(csv_filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp_seconds", "force_value"])
        for t, f in zip(timestamps, forces):
            writer.writerow([t, f])

    # ---- SAVE FULL GRAPH ----
    current_xlim = ax.get_xlim()
    current_ylim = ax.get_ylim()

    ax.set_xlim(0, timestamps[-1])
    ax.set_ylim(min(forces) - 1, max(forces) + 1)

    fig.savefig(png_filename, dpi=300)

    ax.set_xlim(current_xlim)
    ax.set_ylim(current_ylim)

    print(f"\n✔ CSV saved: {csv_filename}")
    print(f"✔ Full graph image saved: {png_filename}\n")


def on_close(event):
    print("\nWindow closed — exporting CSV and full graph...")
    save_csv_and_image()

    if conn:
        conn.close()
    ser.close()


fig.canvas.mpl_connect("close_event", on_close)


# -------------------------------------------------------
#          REAL-TIME SERIAL DATA UPDATE
# -------------------------------------------------------


def update(frame):
    global start_time

    while ser.in_waiting:
        try:
            raw = ser.readline().decode().strip()
            value = float(raw)
        except:
            continue

        t = time.time() - start_time

        timestamps.append(t)
        forces.append(value)

        if conn:
            insert_force(conn, value)

    if len(forces) > 1:
        line.set_data(timestamps, forces)
        ax.set_xlim(max(0, timestamps[-1] - 10), timestamps[-1] + 1)
        ax.set_ylim(min(forces) - 1, max(forces) + 1)

    return (line,)


# -------------------------------------------------------
#                  RUN PLOT
# -------------------------------------------------------
ani = animation.FuncAnimation(fig, update, interval=10)
plt.show()
