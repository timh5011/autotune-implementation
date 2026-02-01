# autotune-implementation

Implementation of autotune on audio input from scratch.

## Contents
 * [User Instructions](#user-instructions)
 * [Theoretical Background](#theoretical-background)

## User Instructions

1. ```pip install sounddevice numpy matplotlib scipy```

2. ```python live_viz.py ```

## Theoretical Background
### Fourier Analysis in Signal Processing

The Fourier Transform maps a function $\phi$ from the time domain to its dual (?) $\hat{\phi}$ frequency domain (the dual space).

The Fourier Transform is defined as $$\hat{\phi}(k) = \int_{-\infty}^{\infty} \phi(x) \exp(-ikx) \, dx$$

and the Inverse Fourier Transform is defined 

### The Numerical Approach: Discrete Fourier Transform

We sample points from $\phi(x)$. The Sampling Theorem tells us

The Discrete Fourier Transform is

$$X_k = \sum _{n=0}^{N-1}x_n\exp\left( -\frac{i2\pi}{N}kn \right) = \langle x|k\rangle  = \langle \text{sample}|\text{frequency mode k}\rangle$$

### Cooley-Tukey Algorithm for Fast Fourier Transform

The computational cost of this approach is very expensive ~O$(n^2)$