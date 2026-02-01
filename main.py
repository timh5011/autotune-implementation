import numpy as np
from cooley_tukey import fft

# Read in audio data from local computer audio input
rate, audio = wavfile.read("my_recording.wav")

# Take the first 1024 samples for your Cooley-Tukey test
test_chunk = audio[0:1024]


# Process audio data using Cooley-Tukey FFT algorithm
