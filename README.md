# autotune-implementation

Implementation of autotune on audio input from scratch.

## Fourier

$\phi(x) = \sum_{n=-\infty}^{\infty} c_n\exp\left( \frac{in\pi x}{l} \right)$

where $c_n = \frac{1}{2l}\int dx \phi(x)\exp\left( \frac{-in\pi x}{l} \right) $ 