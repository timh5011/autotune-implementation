# autotune-implementation

Implementation of autotune on audio input from scratch.


## Background Theory
### Fourier Series

$\phi(x) = \sum _{n=-\infty}^{\infty} c_n\exp\left( \frac{in\pi x}{l} \right)$

where $c_n = \frac{1}{2l}\int _{-l}^{l} dx \text{ }\phi(x)\exp\left( \frac{-in\pi x}{l} \right). $ 