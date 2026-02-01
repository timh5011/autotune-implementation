import sys
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import queue

# --- Settings ---
SAMPLE_RATE = 44100   # Hz
WINDOW_SIZE = 1000    # How many samples to show in the window (zoom level)
DOWNSAMPLE = 1        # If laggy, set to 10 to skip samples

# A queue to transfer data between the audio thread and the plot thread
q = queue.Queue()

def audio_callback(indata, frames, time, status):
    """
    This is called by sounddevice in a separate thread whenever
    there is new audio data.
    """
    if status:
        print(status, file=sys.stderr)
    
    # We only care about the first channel (mono) for now
    # indata is shape (frames, channels)
    q.put(indata[::DOWNSAMPLE, 0])

def update_plot(frame):
    """
    This is called by matplotlib to update the graph.
    """
    global plotdata
    
    while True:
        try:
            data = q.get_nowait()
        except queue.Empty:
            break
        
        # Shift old data left
        shift = len(data)
        plotdata = np.roll(plotdata, -shift, axis=0)
        
        # Put new data on the right
        plotdata[-shift:] = data

    # Update the line on the graph
    line.set_ydata(plotdata)
    return line,

# --- Main Setup ---

# 1. Create a buffer to hold the audio data for plotting
length = int(WINDOW_SIZE * SAMPLE_RATE / (1000 * DOWNSAMPLE)) # Just an estimation buffer
plotdata = np.zeros(WINDOW_SIZE)

# 2. Setup the Plot
fig, ax = plt.subplots()
line, = ax.plot(plotdata)

# Make it look nice
ax.set_ylim([-1.0, 1.0]) # Audio acts usually between -1 and 1
ax.set_xlim([0, WINDOW_SIZE])
ax.set_ylabel("Amplitude")
ax.set_title("Live Audio Input")
ax.grid(True)

# 3. Start the Audio Stream
# We use a context manager so it closes cleanly when you exit
try:
    stream = sd.InputStream(
        channels=1,
        samplerate=SAMPLE_RATE,
        callback=audio_callback
    )
    
    # 4. Start the Animation
    ani = animation.FuncAnimation(
        fig, 
        update_plot, 
        interval=30, # Update every 30ms (approx 30 fps)
        blit=True
    )
    
    print("Listening... Close the window to stop.")
    with stream:
        plt.show()

except Exception as e:
    print(str(e))