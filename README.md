# autotune-implementation

Implementation of autotune on audio input from scratch.

## Fourier

$\phi(x) = \frac{A_0}{2} + \sum_{n}\left (  A_n \cos\frac{n\pi x}{l} + B_n \sin\frac{n\pi x}{l} \right )$

where $ A_n = \frac{1}{l}\int_{-l}{l}dx\text{ }\phi(x)\cos\frac{n\pi x}{l} \text{ for } n = 0,1,2,\dots $ and 
$B_n = \frac{1}{l}\int_{-l}{l}dx\text{ }\phi(x)\sin\frac{n\pi x}{l}\text{ for } n = 1,2,\dots  $