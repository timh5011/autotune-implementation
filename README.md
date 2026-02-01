# autotune-implementation

Implementation of autotune on audio input from scratch.

## Contents
 * [User Instructions](#user-instructions)
 * [Theoretical Background](#theoretical-background)

## User Instructions

1. `pip install sounddevice numpy matplotlib scipy`
2. `python live_viz.py`

## Theoretical Background

### Fourier Analysis in Signal Processing

The Fourier Transform maps a function $\phi$ from the time domain to its dual frequency domain $\hat{\phi}$ (the dual space).

The Fourier Transform is defined as:

$$
\hat{\phi}(k) = \int_{-\infty}^{\infty} \phi(x) \exp(-ikx) \, dx
$$

And the Inverse Fourier Transform is defined similarly, reversing the mapping back to the time domain.

### The Numerical Approach: Discrete Fourier Transform

We sample discrete points from the continuous signal $\phi(x)$. According to the Nyquist-Shannon Sampling Theorem

The Discrete Fourier Transform (DFT) is:

$$
X_k = \sum_{n=0}^{N-1} x_n \exp\left( -\frac{i 2\pi}{N} kn \right) = \langle x | k \rangle
$$

Here, $\langle x | k \rangle$ represents the inner product of our audio samples with the $k$-th frequency mode.

### Cooley-Tukey Algorithm for Fast Fourier Transform

The computational cost of the naive DFT approach is very expensive