import numpy as np

# Implementation of FFT using Cooley-Tukey algorithm.
#
# The README derives the recursive split:
#
#   X_k = E_k + W_N^k * O_k
#
# where E is the DFT of the even-indexed samples and O the DFT of the odd-indexed
# ones. This file implements the *iterative* version of that recursion, which is
# the same arithmetic done bottom-up instead of top-down.
#
# --- Why bit-reversal ordering? ---
#
# The recursion keeps splitting the input by "is the index even or odd", i.e. by
# the LOWEST bit of the index. Then it recurses and splits each half by the next
# lowest bit, and so on. So after all log2(N) levels of splitting, the sample
# that ends up in leaf position p is the sample whose index has the bits of p in
# reverse order: the first split was decided by bit 0, so bit 0 of the original
# index becomes the *most* significant bit of the leaf position.
#
# For N = 8, tracking where each sample lands:
#
#   input     0 1 2 3 4 5 6 7
#   split     evens: 0 2 4 6      | odds: 1 5 3 7 -> (1 5) (3 7)
#   again     (0 4) (2 6)         | (1 5) (3 7)
#
#   index 1 = 001 -> lands at position 100 = 4
#   index 3 = 011 -> lands at position 110 = 6
#   index 6 = 110 -> lands at position 011 = 3
#
# So instead of actually recursing and allocating sub-arrays, we permute the
# input once by reversing the bits of every index. That drops the samples
# directly into their leaf positions, and from there we can merge pairs, then
# quadruples, then octets, entirely in place: every butterfly's two inputs are
# already sitting next to each other. That is the whole trick.

__all__ = ["fft", "ifft", "dft", "magnitude_spectrum", "bit_reversal_indices"]


def bit_reversal_indices(n):
    """Return the permutation `rev` where rev[i] is i with its bits reversed.

    `n` must be a power of two. Reversal is done over log2(n) bits, so for
    n = 8, index 1 (001) maps to 4 (100).
    """
    bits = n.bit_length() - 1
    idx = np.arange(n, dtype=np.int64)
    rev = np.zeros(n, dtype=np.int64)
    for b in range(bits):
        # Peel off bit b of every index (LSB first) and push it into `rev`
        # from the bottom, so the first bit peeled ends up at the top.
        rev = (rev << 1) | ((idx >> b) & 1)
    return rev


def _next_power_of_two(n):
    return 1 << (n - 1).bit_length() if n > 1 else 1


def _prepare(x, pad):
    """Coerce input to a 1-D complex array whose length is a power of two."""
    a = np.asarray(x, dtype=np.complex128).ravel()
    n = a.size
    if n == 0:
        raise ValueError("input is empty")
    if n & (n - 1) != 0:  # not a power of two
        if not pad:
            raise ValueError(
                f"length {n} is not a power of two (pass pad=True to zero-pad)"
            )
        padded = np.zeros(_next_power_of_two(n), dtype=np.complex128)
        padded[:n] = a
        a = padded
    return a


def fft(x, pad=True):
    """Forward DFT of a 1-D signal via the iterative Cooley-Tukey algorithm.

    Returns the complex coefficients X_0 .. X_{N-1} in the usual numpy ordering
    (bin k corresponds to frequency k * sample_rate / N; bins above N/2 are the
    negative frequencies).

    Runs in O(N log N). If `pad` is True, inputs whose length is not a power of
    two are zero-padded up to the next one, which changes N and therefore the
    bin spacing -- check `len(result)`, don't assume it matches `len(x)`.
    """
    a = _prepare(x, pad)
    n = a.size

    # Step 1: drop every sample into its leaf position (see note at top).
    a = a[bit_reversal_indices(n)]

    # Step 2: merge upwards. Stage `size` combines two DFTs of length size/2
    # that are already sitting side by side into one DFT of length `size`.
    size = 2
    while size <= n:
        half = size // 2

        # Twiddle factors for this stage: W_size^j = exp(-2*pi*i*j/size).
        # Only the first half is needed, because W_size^(j + size/2) = -W_size^j
        # -- the periodicity the README points out, and the reason each
        # butterfly produces two outputs from one multiplication.
        w = np.exp(-2j * np.pi * np.arange(half) / size)

        # View the array as (num_blocks, size) so every row is one merge.
        # reshape on a contiguous array gives a view, so writes land in `a`.
        blocks = a.reshape(-1, size)
        even = blocks[:, :half].copy()  # E_k, copied since we overwrite it
        odd = blocks[:, half:] * w      # W^k * O_k

        blocks[:, :half] = even + odd   # X_k
        blocks[:, half:] = even - odd   # X_{k + size/2}

        size *= 2

    return a


def ifft(X, pad=True):
    """Inverse DFT, built from `fft` via the conjugate trick.

    conj(fft(conj(X))) / N equals the inverse transform, since inverting only
    flips the sign of the exponent and adds the 1/N normalisation.
    """
    a = _prepare(X, pad)
    return np.conjugate(fft(np.conjugate(a), pad=False)) / a.size


def dft(x):
    """Naive O(N^2) DFT. Only here as a reference to check `fft` against."""
    a = np.asarray(x, dtype=np.complex128).ravel()
    n = a.size
    k = np.arange(n).reshape(-1, 1)  # frequency index, one per row
    m = np.arange(n).reshape(1, -1)  # sample index, one per column
    return np.exp(-2j * np.pi * k * m / n) @ a


def magnitude_spectrum(samples, sample_rate, window=True):
    """Convenience wrapper for the live visualisers.

    Takes a block of real audio samples and returns `(freqs, mags)` for the
    non-negative frequencies only: `freqs` in Hz, `mags` the magnitude of each
    bin scaled so a pure tone of amplitude A reads roughly A.

    `window=True` applies a Hann window first, which suppresses the spectral
    leakage you get from chopping a continuous signal into blocks.
    """
    a = np.asarray(samples, dtype=np.float64).ravel()
    gain = a.size  # sum of the (rectangular) window
    if window and a.size > 1:
        w = np.hanning(a.size)
        a = a * w
        gain = w.sum()  # Hann only passes ~half the energy; undo that below

    spectrum = fft(a)
    n = spectrum.size
    half = n // 2 + 1

    freqs = np.arange(half) * (sample_rate / n)
    # Factor 2 because we fold the negative frequencies onto the positive ones.
    # Dividing by the window gain (not the padded length) keeps a tone of
    # amplitude A reading as A regardless of windowing or zero-padding.
    mags = np.abs(spectrum[:half]) * (2.0 / gain)
    mags[0] /= 2.0  # DC has no mirrored twin
    if n % 2 == 0:
        mags[-1] /= 2.0  # neither does Nyquist

    return freqs, mags


if __name__ == "__main__":
    rng = np.random.default_rng(0)

    # Power-of-two input against numpy's FFT and against the naive DFT.
    x = rng.standard_normal(1024)
    print("vs np.fft :", np.max(np.abs(fft(x) - np.fft.fft(x))))
    print("vs dft    :", np.max(np.abs(fft(x[:64]) - dft(x[:64]))))

    # Round trip.
    print("ifft(fft) :", np.max(np.abs(ifft(fft(x)) - x)))

    # Non-power-of-two input gets zero-padded, so compare against numpy padded
    # to the same length (live_viz uses WINDOW_SIZE = 1000).
    y = rng.standard_normal(1000)
    print("padded    :", np.max(np.abs(fft(y) - np.fft.fft(y, 1024))))

    # Sanity check the helper on a known tone.
    sr = 44100
    t = np.arange(4096) / sr
    tone = 0.5 * np.sin(2 * np.pi * 440.0 * t)
    freqs, mags = magnitude_spectrum(tone, sr)
    print("peak      :", f"{freqs[np.argmax(mags)]:.1f} Hz", f"amp {mags.max():.3f}")
