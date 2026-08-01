# autotune-implementation

Implementation of autotune on live audio input from scratch.

## Contents
 * [User Instructions](#user-instructions)
 * [Theoretical Background](#theoretical-background)

## User Instructions

1. `pip install sounddevice numpy matplotlib scipy`
2. `python live_viz.py`

## Theoretical Background

### Fourier Analysis in Signal Processing

We are given some audio signal $\ket{x} = \phi$ and wish to decompose it into the different frequencies making it up. We can do this by representing this signal vector in the orthonormal basis of freqencies $\ket{k} = \exp(ikx)$, for integers $k$. We get 

$$
\ket{x} = \int_{-\infty}^{\infty}\hat{\phi}(k)\ket{k} \ dk
$$

The Fourier Transform allows us to solve for the coefficients by mapping the function $\phi$ from the time domain to the frequency domain $\hat{\phi}$.

The Fourier Transform is defined as:

$$
\hat{\phi}(k) = \int_{-\infty}^{\infty} \phi(x) \exp(-ikx) \ dx = \langle x | k \rangle
$$

Here, $\langle x | k \rangle$ represents the inner product of our audio samples with the $k$-th frequency mode.

And the Inverse Fourier Transform is defined similarly, reversing the mapping back to the time domain.

### The Numerical Approach: Discrete Fourier Transform

We sample discrete points from the continuous signal $\phi(x)$. According to the Nyquist-Shannon Sampling Theorem ...

The Discrete Fourier Transform is:

$$
X_k = \sum_{n=0}^{N-1} x_n \exp\left( -\frac{i 2\pi}{N} kn \right)
$$

The job of performing a Fourier Transform comes down to computing the coefficient $X_k$ for all frequencies $k$. If there are $N$ and (?) $N$ samples, each frequency computation requires $N$ multiplications, and thus the runtime of this procedure is $O(N^2)$. 

### Cooley-Tukey Algorithm for Fast Fourier Transform

The computational cost of the naive DFT approach is very expensive. Fast-Fourier-Transform exploits the fact that the twiddle factors $W_N^n = \exp\left( -\frac{i 2\pi}{N} kn \right)$ are periodic to perform the same transformation in $O(N\log{N})$ time. Notice $W_N^{n+N/2} = - W_N^n$. 


$$
\begin{aligned}
X_k &= \sum_{n=0}^{N-1} x_n \exp\left( -\frac{i 2\pi}{N} kn \right) \\
&= \sum_{n \text{ even}} x_n \exp\left( -\frac{i 2\pi}{N} kn \right) + \sum_{n \text{ odd}} x_n \exp\left( -\frac{i 2\pi}{N} kn \right) \\
&= \sum_{m=0}^{N/2-1} x_{2m} \exp\left( -\frac{i 2\pi}{N/2} km \right) + \exp\left(-\frac{i 2\pi}{N} k\right) \sum_{m=0}^{N/2-1} x_{2m+1} \exp\left( -\frac{i 2\pi}{N/2} km \right)
\end{aligned}
$$

which is $X_k = E_k + W_N^k O_k$, where $E$ is the DFT of the even-indexed samples and $O$ the DFT of the odd-indexed ones. Because $W_N^{k + N/2} = -W_N^k$, the same two half-transforms also give $X_{k + N/2} = E_k - W_N^k O_k$ for free. One complex multiplication yields two output coefficients — this pairing is called a **butterfly**.

### Bit-Reversal Ordering

The recursion above splits the samples by *even vs. odd index*, which is to say by the **lowest bit** of the index. Each half is then split by the next-lowest bit, and so on for all $\log_2 N$ levels. So the sample that ends up in leaf position $p$ is the one whose index is $p$ **with its bits written backwards**: the first split was decided by bit 0, so bit 0 of the original index becomes the most significant bit of the final position.

For $N = 8$:

| index | binary | reversed | position |
|---|---|---|---|
| 1 | 001 | 100 | 4 |
| 3 | 011 | 110 | 6 |
| 6 | 110 | 011 | 3 |

```
input     x0 x1 x2 x3 x4 x5 x6 x7
by bit 0  (x0 x2 x4 x6) (x1 x3 x5 x7)
by bit 1  (x0 x4)(x2 x6) (x1 x5)(x3 x7)
```

This matters because it lets us throw the recursion away. Rather than descending the tree and allocating sub-arrays at every level, we permute the input **once** by reversing the bits of every index. That drops each sample straight into its leaf position, and we then rebuild bottom-up: merge adjacent pairs into 2-point DFTs, those into 4-point DFTs, and so on. At every stage the two inputs to each butterfly are already adjacent in memory, so the whole transform runs in place with no copying.

There are $\log_2 N$ stages and $N/2$ butterflies per stage, giving the $O(N \log N)$ cost. Note this construction requires $N$ to be a power of two; `cooley_tukey.fft` zero-pads up to the next one when it isn't (`live_viz`'s 1000-sample window becomes 1024).
