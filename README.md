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

We are given some audio signal $\ket{x} = \phi(x)$ and wish to decompose it into the different frequencies making it up. We can do this by representing this signal vector in the orthonormal basis of freqencies $\ket{k} = \exp(ikx)$, for integers $k$. We get 

$$
\ket{x} = \int_{-\infty}^{\infty}\hat{\phi}(k)\ket{k} \ dx
$$

The Fourier Transform allows us to solve for the coefficients by mapping the function $\phi$ from the time domain to the frequency domain $\hat{\phi}$.

The Fourier Transform is defined as:

$$
\hat{\phi}(k) = \int_{-\infty}^{\infty} \phi(x) \exp(-ikx) \ dx = \langle x | k \rangle
$$

Here, $\langle x | k \rangle$ represents the inner product of our audio samples with the $k$-th frequency mode.

And the Inverse Fourier Transform is defined similarly, reversing the mapping back to the time domain.

### The Numerical Approach: Discrete Fourier Transform

We sample discrete points from the continuous signal $\phi(x)$. According to the Nyquist-Shannon Sampling Theorem

The Discrete Fourier Transform (DFT) is:

$$
X_k = \sum_{n=0}^{N-1} x_n \exp\left( -\frac{i 2\pi}{N} kn \right)
$$

The job of performing a Fourier Transform comes down to computing the coefficient $X_k$ for all frequencies $k$. If there are $N$ and (?) $N$ samples, each of these computations requires $N^2$ multiplications, and thus the runtime of this procedure is $O(N^2)$. 

### Cooley-Tukey Algorithm for Fast Fourier Transform

The computational cost of the naive DFT approach is very expensive. Fast-Fourier-Transform exploits the fact that the twiddle factors $W_N^n = \exp\left( -\frac{i 2\pi}{N} kn \right)$ are periodic. Notice $W_N^{n+N/2} = - W_N^n$. 


$$
\begin{aligned}
X_k &= \sum_{n=0}^{N-1} x_n \exp\left( -\frac{i 2\pi}{N} kn \right) \\
&= \sum_{n \text{even}} x_n \exp\left( -\frac{i 2\pi}{N} kn \right) + \sum_{n \text{odd}} x_n \exp\left( -\frac{i 2\pi}{N} kn \right) \\
&= \sum_{m=0}^{N/2-1} x_{2m} \exp\left( -\frac{i 2\pi}{N/2} km \right) + \exp\left(-\frac{i 2\pi}{N} k\right) \sum_{m=0}^{N/2-1} x_{2m+1} \exp\left( -\frac{i 2\pi}{N/2} km \right)
\end{aligned}
$$
