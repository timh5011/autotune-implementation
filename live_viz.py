import sys
import os  # Added to handle directory creation
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import queue
import scipy.io.wavfile as wavfile

# --- Settings ---
SAMPLE_RATE = 44100   
WINDOW_SIZE = 1000    
DOWNSAMPLE = 1        
OUTPUT_FILENAME = "my_recording.wav"
OUTPUT_FOLDER = "audio_data"  # New folder name

# 1. The Queue for Visualization (Fast, throws away old data)
viz_queue = queue.Queue()

# 2. The List for Storage (Keeps everything)
full_recording = []

def audio_callback(indata, frames, time, status):
    """
    Called by the audio thread. 
    1. Pushes data to the visualizer.
    2. Appends data to our storage buffer.
    """
    if status:
        print(status, file=sys.stderr)
    
    # Get the mono channel data
    mono_data = indata[:, 0]
    
    # Path A: Visualization
    viz_queue.put(mono_data[::DOWNSAMPLE])
    
    # Path B: Storage
    full_recording.append(mono_data.copy())

def update_plot(frame):
    global plotdata
    while True:
        try:
            data = viz_queue.get_nowait()
        except queue.Empty:
            break
        
        shift = len(data)
        plotdata = np.roll(plotdata, -shift, axis=0)
        plotdata[-shift:] = data

    line.set_ydata(plotdata)
    return line,

# --- Main Execution ---

# Setup Plotting Buffer
plotdata = np.zeros(WINDOW_SIZE)

fig, ax = plt.subplots()
line, = ax.plot(plotdata)
ax.set_ylim([-0.5, 0.5]) 
ax.set_xlim([0, WINDOW_SIZE])
ax.set_ylabel("Amplitude")
ax.set_title("Live Input (Recording...)")
ax.grid(True)

try:
    # Start the Stream
    stream = sd.InputStream(
        channels=1,
        samplerate=SAMPLE_RATE,
        callback=audio_callback
    )
    
    ani = animation.FuncAnimation(
        fig, 
        update_plot, 
        interval=30, 
        blit=True
    )
    
    print(f"Recording... Close the plot window to save.")
    
    with stream:
        plt.show() # Code hangs here until window is closed

    # --- Post-Processing (After Window Closes) ---
    print("\nProcessing recording...")
    
    if len(full_recording) > 0:
        concatenated_audio = np.concatenate(full_recording)
        
        print(f"Recorded {len(concatenated_audio)} samples.")
        print(f"Duration: {len(concatenated_audio)/SAMPLE_RATE:.2f} seconds.")

        # --- NEW: Create Directory and Save Path ---
        # 1. Create the folder if it doesn't exist
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        
        # 2. Build the full path
        full_path = os.path.join(OUTPUT_FOLDER, OUTPUT_FILENAME)

        # 3. Save to WAV file
        wav_data = (concatenated_audio * 32767).astype(np.int16)
        wavfile.write(full_path, SAMPLE_RATE, wav_data)
        
        print(f"Saved to: {full_path}")
        
    else:
        print("No audio recorded.")

except Exception as e:
    print(str(e))