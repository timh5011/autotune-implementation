import sys
import os  # Added to handle directory creation
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import queue
import scipy.io.wavfile as wavfile

from cooley_tukey import magnitude_spectrum

# --- Settings ---
SAMPLE_RATE = 44100
WINDOW_SIZE = 1000
DOWNSAMPLE = 1
OUTPUT_FILENAME = "my_recording.wav"
OUTPUT_FOLDER = "audio_data"  # New folder name

# FFT settings. FFT_SIZE must be a power of two (otherwise fft() zero-pads and
# the bin spacing stops matching what we label the axis with). 4096 samples is
# ~93 ms of audio, giving ~10.8 Hz bins -- long enough to resolve a pitch,
# short enough to still feel live.
FFT_SIZE = 4096
FREQ_LIMIT = 5000     # Hz, upper edge of the spectrum plot
DB_FLOOR = -100       # quietest magnitude drawn, in dB

# If DOWNSAMPLE > 1 the visualiser sees a slower stream, so the frequency axis
# has to be scaled to match. (Note this also aliases anything above the new
# Nyquist rate, since we aren't low-pass filtering before dropping samples.)
EFFECTIVE_RATE = SAMPLE_RATE / DOWNSAMPLE

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
    global audiobuffer
    while True:
        try:
            data = viz_queue.get_nowait()
        except queue.Empty:
            break

        shift = len(data)
        audiobuffer = np.roll(audiobuffer, -shift, axis=0)
        audiobuffer[-shift:] = data

    # Left panel: the most recent WINDOW_SIZE samples of the same buffer.
    wave_line.set_ydata(audiobuffer[-WINDOW_SIZE:])

    # Right panel: our own Cooley-Tukey FFT over the whole buffer.
    _, mags = magnitude_spectrum(audiobuffer, EFFECTIVE_RATE)
    db = 20.0 * np.log10(np.maximum(mags[plot_bins], 1e-12))
    spec_line.set_ydata(np.maximum(db, DB_FLOOR))

    # Loudest bin above 50 Hz -- a crude pitch readout to build on later.
    peak = pitch_bins[np.argmax(mags[pitch_bins])]
    if mags[peak] > 1e-3:
        peak_text.set_text(f"peak: {freqs[peak]:6.1f} Hz")
    else:
        peak_text.set_text("peak:    -- Hz")

    return wave_line, spec_line, peak_text

# --- Main Execution ---

# One rolling buffer feeds both plots: the waveform shows its tail, the
# spectrum uses all of it.
audiobuffer = np.zeros(FFT_SIZE)

# Bin centres are fixed because the buffer length is, so compute them once.
freqs, _ = magnitude_spectrum(audiobuffer, EFFECTIVE_RATE)
plot_bins = freqs <= FREQ_LIMIT              # what we draw
pitch_bins = np.flatnonzero(freqs >= 50.0)   # what we search for a peak

fig, (ax_wave, ax_spec) = plt.subplots(1, 2, figsize=(12, 4.5))

# Left: time domain
wave_line, = ax_wave.plot(audiobuffer[-WINDOW_SIZE:])
ax_wave.set_ylim([-0.5, 0.5])
ax_wave.set_xlim([0, WINDOW_SIZE])
ax_wave.set_xlabel("Sample")
ax_wave.set_ylabel("Amplitude")
ax_wave.set_title("Time Domain (Recording...)")
ax_wave.grid(True)

# Right: frequency domain
spec_line, = ax_spec.plot(freqs[plot_bins], np.full(plot_bins.sum(), DB_FLOOR))
ax_spec.set_ylim([DB_FLOOR, 0])
ax_spec.set_xlim([0, FREQ_LIMIT])
ax_spec.set_xlabel("Frequency (Hz)")
ax_spec.set_ylabel("Magnitude (dB)")
ax_spec.set_title(f"Frequency Domain ({FFT_SIZE}-point FFT)")
ax_spec.grid(True)

# animated=True keeps this out of the static background so blitting redraws it.
peak_text = ax_spec.text(
    0.97, 0.94, "peak:    -- Hz",
    transform=ax_spec.transAxes, ha="right", va="top",
    family="monospace", animated=True,
)

fig.tight_layout()

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