import sys
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import queue

from cooley_tukey import magnitude_spectrum

# --- Settings ---
SAMPLE_RATE = 44100   # Hz
WINDOW_SIZE = 1000    # How many samples to show in the window (zoom level)
DOWNSAMPLE = 1        # If laggy, set to 10 to skip samples

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
    This is called by matplotlib to update the graphs.
    """
    global audiobuffer

    while True:
        try:
            data = q.get_nowait()
        except queue.Empty:
            break

        # Shift old data left
        shift = len(data)
        audiobuffer = np.roll(audiobuffer, -shift, axis=0)

        # Put new data on the right
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

# --- Main Setup ---

# 1. One rolling buffer feeds both plots: the waveform shows its tail, the
#    spectrum uses all of it.
audiobuffer = np.zeros(FFT_SIZE)

# Bin centres are fixed because the buffer length is, so compute them once.
freqs, _ = magnitude_spectrum(audiobuffer, EFFECTIVE_RATE)
plot_bins = freqs <= FREQ_LIMIT              # what we draw
pitch_bins = np.flatnonzero(freqs >= 50.0)   # what we search for a peak

# 2. Setup the Plots
fig, (ax_wave, ax_spec) = plt.subplots(1, 2, figsize=(12, 4.5))

# Left: time domain
wave_line, = ax_wave.plot(audiobuffer[-WINDOW_SIZE:])
ax_wave.set_ylim([-1.0, 1.0]) # Audio acts usually between -1 and 1
ax_wave.set_xlim([0, WINDOW_SIZE])
ax_wave.set_xlabel("Sample")
ax_wave.set_ylabel("Amplitude")
ax_wave.set_title("Time Domain")
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