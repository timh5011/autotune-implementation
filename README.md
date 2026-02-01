# autotune-implementation

Implementation of autotune on audio input from scratch.

## Contents
 * [User Instructions](#user-instructions)
 * [Theoretical Background](#theoretical-background)

## User Instructions

1. ```pip install sounddevice numpy matplotlib scipy```

2. ```python live_viz.py ```

## Theoretical Background
### Fourier Series

Any (analytic?) (periodic?) function $\phi$ on interval $\[-l,l\]\in\mathbb{R}$ can be expressed as the series

$$ \phi(x) = \sum _{n=-\infty}^{\infty} c_n\exp\left( \frac{in\pi x}{l} \right) $$

where $$ c_n = \frac{1}{2l}\exp\left( \frac{-in\pi x}{l} \right). $$

The Fourier Transform maps the function $\phi$ from the time domain to its dual (?) $\hat{\phi}$ frequency domain (the dual space).

The Fourier Transform is defined as $ \hat{\phi}(k) = \int _{-\infty}^{\infty} dx\text{ }\phi(x)\exp\left( \frac{-in\pi x}{l} \right). $

and the Inverse Fourier Transform is defined.

### The Numerical Approach: Discrete Fourier Transform

We sample points from $\phi(x)$. The Sampling Theorem tells us

The Discrete Fourier Transform is

$$ X_k = \sum _{n=0}^{N-1}x_n\exp\left( -\frac{i2\pi}{N}kn \right) = \langle x|k\rangle  = \langle \text{sample}|\text{frequency mode k}\rangle $$

### Cooley-Tukey Algorithm for Fast Fourier Transform

The computational cost of this approach is very expensive ~$O(n^2)$