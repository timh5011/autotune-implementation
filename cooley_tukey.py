import numpy as np

# Implementation of FFT using Cooley-Tukey algorithm

# Okay so to compute the fourier coefficnents we are taking the dot product of the signal with different frequency basis vectors (exponentials)
# We can reorder the samples by the bit-reversal permutation
# The point of this is is that these samples will be dotted with essentially the same basis vectors (sign chance)?
# The reason for this is due to the periodicity of the complex exponentials (basis vectors)
# I'm not totally sure how separating the samples by even and odd indicies corresponds to this periodicity

