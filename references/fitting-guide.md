# XAFS Fitting Methodology Guide

## EXAFS Equation

The standard EXAFS equation for a single scattering path:

$$\chi(k) = S_0^2 \sum_i \frac{N_i |f_i(k)|}{k R_i^2} \exp(-2\sigma_i^2 k^2) \exp\left(-\frac{2R_i}{\lambda(k)}\right) \sin(2kR_i + \phi_i(k))$$

Where:
- $S_0^2$ = amplitude reduction factor (typically 0.7-1.0)
- $N_i$ = coordination number of path $i$
- $R_i$ = half path length (bond distance)
- $\sigma_i^2$ = Debye-Waller factor (mean-square relative displacement)
- $|f_i(k)|$ = backscattering amplitude
- $\phi_i(k)$ = phase shift
- $\lambda(k)$ = photoelectron mean free path

## Feff Path Selection

### Path Types

1. **Single Scattering (SS)**: Photoelectron scatters from one neighboring atom
   - Most important for first-shell EXAFS
   - example: Mo -> O -> back (Mo-O path)

2. **Multiple Scattering (MS)**: Photoelectron scatters from multiple atoms
   - Important for collinear geometries
   - example: Mo -> O -> Mo -> O -> back (focusing effect)

### Path Ranking

Order paths by amplitude (degeneracy * |f(k)| / R^2):
1. First shell: lowest R, often highest amplitude
2. Second shell: moderate R
3. Higher shells: contributions decay with R and sigma^2

### Typical Parameters

| Shell | R range (Ang) | N range | sigma^2 (Ang^2) |
|-------|---------------|---------|-----------------|
| 1st   | 1.5 - 2.5    | 2-6     | 0.001 - 0.010   |
| 2nd   | 2.5 - 4.0    | 2-12    | 0.002 - 0.015   |
| 3rd   | 3.5 - 5.0    | 2-24    | 0.003 - 0.020   |

## Fit Quality Metrics

### R-factor

$$R = \frac{\sum [\chi_{data}(k) - \chi_{fit}(k)]^2}{\sum \chi_{data}(k)^2}$$

- R < 0.02: Excellent fit
- R < 0.05: Good fit
- R < 0.10: Acceptable fit
- R > 0.10: Poor fit, consider revising model

### Reduced Chi-Square

$$\chi^2_\nu = \frac{\chi^2}{N_{indep} - N_{var}} = \frac{\sum [k^w(\chi_{data} - \chi_{fit})]^2}{N_{indep} - N_{var}}$$

Desired: $\chi^2_\nu \approx 1$

### Number of Independent Points

$$N_{indep} = \frac{2 \Delta k \Delta R}{\pi}$$

Constraint: $N_{var} \leq \frac{2}{3} N_{indep}$ (Information Theory limit)

## Data Processing Steps

1. **Energy calibration**: Align E0 to known standard
2. **Pre-edge subtraction**: Remove background below edge
3. **Normalization**: Normalize edge jump to 1
4. **Background removal**: AUTOBK or similar (Rbkg ~ 1.0 Ang)
5. **k-weight selection**: k^1 (light scatterers), k^2 (standard), k^3 (heavy scatterers)
6. **Fourier transform**: chi(k) -> chi(R)
7. **Back-transform**: Isolate shell contributions for fitting

## Parameter Constraints

### Physical Constraints
- N must be positive and physically meaningful
- sigma^2 must be positive (negative means unphysical)
- R must be positive and consistent with known bond lengths

### Mathematical Constraints
- Number of free parameters <= N_indep
- Parameters should not be near bounds after fitting
- Correlated parameters (>0.9) should be constrained or merged

## Common Pitfalls

1. **Too many parameters**: Fitting too many variables with limited data
2. **Correlated parameters**: N and sigma^2 are often correlated
3. **Missing paths**: Important scattering paths omitted from model
4. **Incorrect E0**: Can shift R values systematically
5. **kT range too narrow**: Limits R-space resolution
