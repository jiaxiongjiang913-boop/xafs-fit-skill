# XAFS Fitting Methodology Guide

## EXAFS Equation — Full Derivation

### From Fermi's Golden Rule to χ(k)

X-ray absorption is a quantum transition from an initial state |i⟩ (x-ray + core
electron + no photoelectron) to a final state |f⟩ (no x-ray + core hole +
photoelectron). The transition probability is given by Fermi's Golden Rule:

$$\mu(E) \propto |\langle i|H|f\rangle|^2$$

where H ∝ e^{ik·r} (the p·A interaction term). The initial state is localized on the
absorbing atom — it is unaffected by neighbors. The final state |f⟩ is perturbed by
neighbor atoms because the photoelectron scatters from them. Splitting:

$$|f\rangle = |f_0\rangle + |\Delta f\rangle$$

where |f₀⟩ is the "bare atom" final state (no neighbors) and |Δf⟩ is the scattered
contribution, yields:

$$\mu(E) = |\langle i|H|f_0\rangle|^2 \left[1 + \frac{\langle i|H|\Delta f\rangle \langle f_0|H|i\rangle^*}{|\langle i|H|f_0\rangle|^2} + C.C.\right]$$

This has the form μ(E) = μ₀(E)[1 + χ(E)], where:

$$\chi(E) \propto \langle i|H|\Delta f\rangle \approx \psi_{scatt}(0)$$

> **Fundamental result**: The EXAFS χ(E) is proportional to the amplitude of the
> scattered photoelectron wavefunction at the absorbing atom.

### Building the EXAFS Equation

The photoelectron propagates as a spherical wave:

$$\psi(k,r) = \frac{e^{ikr}}{kr}$$

With inelastic damping (mean free path λ) and core-hole lifetime:

$$\psi(k,r) = \frac{e^{ikr} e^{-2r/\lambda(k)}}{kr}$$

The round-trip process: absorber → scatterer → absorber:
1. Photoelectron travels R to neighbor: e^{ikR}/kR
2. Scatters with amplitude f(k) and phase δ(k): [2k f(k) e^{iδ(k)}]
3. Returns R back to absorber: e^{ikR}/kR
4. Add complex conjugate for real χ(k)

$$\chi(k) \propto \frac{e^{ikR}}{kR} \cdot [2k f(k) e^{i\delta(k)}] \cdot \frac{e^{ikR}}{kR} + C.C.$$

Which simplifies to the single-shell EXAFS equation:

$$\chi(k) = \frac{N f(k)}{k R^2} e^{-2k^2\sigma^2} e^{-2R/\lambda(k)} \sin[2kR + \delta(k)]$$

Adding S₀² (amplitude reduction) and summing over all shells:

$$\chi(k) = S_0^2 \sum_j \frac{N_j f_j(k)}{k R_j^2} e^{-2k^2\sigma_j^2} e^{-2R_j/\lambda(k)} \sin[2kR_j + \delta_j(k)]$$

### Parameter Physics Deep Dive

#### S₀² — Amplitude Reduction Factor (0.7–1.0)

Physical origin: When a core electron is ejected, the remaining (N−1) electrons
relax to screen the core hole. This multi-electron process reduces the overlap
between initial and final states. S₀² accounts for:
- Intrinsic losses: shake-up (excitation) / shake-off (ionization) of passive electrons
- Typically 0.8–1.0 for K-edges, measured via reference compound with known CN
- Fixed during fitting once calibrated; floating S₀² and CN simultaneously is degenerate

**Calibration approach** (as in the a-MoO3 project):
1. Measure EXAFS of a reference compound with known structure (e.g., Mo metal foil)
2. Feff calculate f(k), δ(k) using known structure
3. Fix CN to the crystallographic value, float S₀²
4. The fitted S₀² applies to all measurements at the same edge on the same beamline

#### Nⱼ — Coordination Number

- Must be positive and physically sensible (integer for well-ordered systems)
- For amorphous/disordered systems, non-integer CN reflects structural disorder
- Standard uncertainty: ±10–20% for well-separated shells
- Anti-correlated with σ² (~90%): both affect oscillation envelope
- CN = S₀²(fitted) / S₀²(true) × (fitted amplitude) / (Feff amplitude)

#### Rⱼ — Interatomic Distance (Å)

- The half-path length; for single scattering, R = bond distance
- Precision: typically ±0.01–0.02 Å for first shell
- FT shows apparent R (phase-uncorrected) shifted ~0.3–0.5 Å shorter than true R
- E₀ error causes systematic R errors: +1 eV E₀ ≈ −0.01 Å R for first shell
- Correlation with E₀: they must be fit together

#### σ²ⱼ — Debye-Waller Factor (Å²)

Physical components:
- **Thermal disorder**: Vibrational motion (∝ T); harmonic at moderate T
- **Static disorder**: Bond length distribution from structural heterogeneity

Typical values:
- First shell covalent: 0.001–0.003 Å² (tight bonds)
- First shell ionic/labile: 0.003–0.008 Å²
- Higher shells: 0.005–0.020 Å² (more disorder at larger distances)
- Liquid/solution: 0.010–0.030 Å²
- Negative σ² is unphysical — indicates model error (missing path, wrong R)

Temperature dependence:
$$\sigma^2(T) = \sigma^2_{static} + \frac{\hbar}{2\mu\omega_E} \coth\left(\frac{\hbar\omega_E}{2k_BT}\right)$$

(Einstein model) or correlated Debye model for more accurate treatment.

#### δⱼ(k) — Scattering Phase Shift

- The phase change when photoelectron scatters from neighbor atom
- Varies with Z: heavier atoms have larger phase shifts
- Causes the apparent R shift in FT magnitude (~0.3–0.5 Å for first shell)
- Feff calculates δ(k) accurately; using raw phase from feffNNNN.dat requires
  central-atom phase correction (handled by FeffPathGroup._calc_chi or IFEFFIT)
- Phase information lives in Re[χ(R)], not |χ(R)| — reason fitting must use complex χ(R)

#### fⱼ(k) — Backscattering Amplitude

- Intrinsic scattering power of neighbor atom, strongly Z-dependent
- Light scatterers (O, N, C): peak at low k (3–5 Å⁻¹), decays quickly
- Heavy scatterers (Fe, Pb): peak at medium–high k (5–8 Å⁻¹), broader distribution
- Allows neighbor Z identification to within ±5
- This is why k-weight choice matters:
  - k¹ for light scatterers (emphasizes low-k where O/N scatter strongly)
  - k² for intermediate (standard, balances all k)
  - k³ for heavy scatterers (emphasizes high-k where metals scatter strongly)

#### λ(k) — Photoelectron Mean Free Path

- Combined effect of inelastic scattering losses + core-hole lifetime
- Typically λ = 5–30 Å, with minimum ~5 Å at k = 3–5 Å⁻¹
- λ(k) has a nearly universal shape: increases roughly as k¹/² at high k
- This is why XAFS is inherently a **local probe**: the e^{−2R/λ} term suppresses
  contributions from atoms beyond ~5–8 Å
- Already included in Feff output files (or can be extracted from feffNNNN.dat)

#### E₀ — Energy Origin Shift

- E₀ is NOT the exact edge position — it's a fitting parameter!
- Absorbs systematic errors in:
  - Experimental energy calibration (~0.5–2 eV)
  - Calculated E₀ from Feff (muffin-tin approximation)
  - Chemical shifts (different oxidation states)
- Should be small: |E₀| < 10 eV typically
- All shells of the same absorber should share a single E₀
- Large fitted E₀ (>10–15 eV) indicates a problem: wrong structural model,
  poor calibration, or missing phase correction
- ΔE₀ and ΔR are correlated; floating E₀ allows R to converge to true value

## Feff Path Selection

### Path Types

1. **Single Scattering (SS)**: Photoelectron scatters from one neighbor and returns
   - Dominant in first-shell EXAFS
   - Degeneracy equals crystallographic multiplicity
   - Example: Mo → O → back (4 equatorial O at 1.73 Å)

2. **Multiple Scattering (MS)**: Photoelectron scatters from 2+ atoms
   - Important for collinear or near-collinear geometries (bond angle > 150°)
   - Focusing effect: forward scattering from intermediate atom amplifies signal
   - Example: Mo → O → Mo → O → back (3-leg MS in Mo-O-Mo chains)
   - Most important in well-ordered crystalline systems

### Path Ranking

Order paths by expected amplitude contribution: amplitude ∝ N × |f(k)| / R²

1. **First shell**: Lowest R, highest amplitude per atom
2. **Second shell**: Moderate R, can be high if many equivalent atoms (e.g., Mo-Mo at 3.5 Å)
3. **Higher shells**: Amplitude decays with R² and σ² — rarely useful beyond 4–5 Å
4. **MS paths**: Only significant for specific geometries; typically ≤10% of total

### Multiple Scattering — When It Matters

- **Collinear chains** (M-O-M'): 3-leg paths can contribute 5–20% of first-shell amplitude
- **Square-planar or linear geometry**: MS contributions are large due to focusing
- **Tetrahedral geometry**: MS is weak (angles far from 180°)
- **Octahedral**: Moderate MS, especially for trans configurations
- MS degneeracy is NOT equal to atomic multiplicity — it's the number of equivalent
  scattering sequences at the same total path length

## R-Space Fitting Theory

### Why R-space Fitting?

The Fourier transform χ(k) → χ(R) separates different coordination shells into
distinct peaks. This provides two key advantages over k-space fitting:

1. **Selective windowing**: By restricting the R-range (e.g., 1.0–2.5 Å), you fit
   only the first coordination shell while ignoring higher shells. In k-space, all
   shells overlap and cannot be separated.

2. **Reduced parameter correlations**: In R-space, parameters for different shells
   are less correlated because their contributions are spatially separated.

3. **Residual inspection**: The R-space residual reveals which shells are poorly fit,
   guiding model improvement.

### Complex vs Magnitude Fitting

**This is critical and often misunderstood.** The Fourier transform χ(R) is a complex
function. The magnitude |χ(R)| is the most common visualization, but it discards phase
information. When fitting:

- **ALWAYS fit both Re[χ(R)] and Im[χ(R)]** — the real part contains the phase
  information that constrains R and E₀
- Fitting only |χ(R)| loses all phase sensitivity, making R and E₀ unconstrained
- The fit in R-space uses the full complex χ(R) when properly configured

### FT Window Function Effects

The finite k-range requires windowing before FT:

- **Hanning**: Softer edges, less ringing, recommended for most cases
- **Kaiser-Bessel**: Sharper cutoff, better resolution but more side-lobes
- **dk parameter**: Width of the window sill (typically 1–2 Å⁻¹)

Window choice affects:
- Peak width in R-space (narrower window → broader peaks)
- Side-lobe artifacts (sharper window → more ringing)
- Apparent peak positions (small shifts possible with different windows)

## Fit Quality Metrics — Detailed

### R-factor

$$R = \frac{\sum_{i} [\chi_{data}(k_i) - \chi_{model}(k_i)]^2}{\sum_{i} \chi_{data}(k_i)^2}$$

- R < 0.01: Exceptional (possibly over-fit — check N_indep)
- R < 0.02: Excellent
- R < 0.05: Good, publishable
- R < 0.10: Acceptable, but examine residual for systematic deviations
- R > 0.10: Model likely incomplete — missing shells or wrong structure
- R is always computed over the FIT RANGE, not the full spectrum

### Reduced Chi-Square

$$\chi^2_\nu = \frac{1}{\nu} \sum_{i=1}^{N} \left[\frac{k_i^w (\chi_{data}(k_i) - \chi_{model}(k_i))}{\epsilon_i}\right]^2$$

where ν = N_indep − N_var (degrees of freedom), and εᵢ is the measurement
uncertainty. χ²_ν ≈ 1 indicates the model matches data within estimated noise.
Values << 1 suggest overestimated noise or over-fitting. Values >> 1 suggest
inadequate model or underestimated noise.

### Number of Independent Points

$$N_{indep} \approx \frac{2 \cdot \Delta k \cdot \Delta R}{\pi}$$

This is the Nyquist-Shannon limit for EXAFS: the number of independent
measurements extractable from the data. **This is an upper bound** — practical
limits are typically lower.

### Information Theory Constraint

$$N_{var} \leq \frac{2}{3} N_{indep}$$

This stricter limit comes from information theory, requiring sufficient data per
parameter for reliable determination. For publication-quality fits, stay under this
threshold.

### Standard Uncertainties (from ε²)

- If measurement uncertainty ε is unknown, it's estimated from the Fourier-filtered
  data noise above R_max (where no structural signal is expected)
- The covariance matrix from the fit gives parameter uncertainties
- These are statistical uncertainties ONLY — systematic errors (choice of Feff model,
  background subtraction, etc.) often dominate

## Parameter Correlation Physics

### CN ↔ σ² (typically r ≈ −0.85 to −0.95)

This is the strongest and most problematic correlation in EXAFS fitting. Both CN
and σ² affect the oscillation envelope (amplitude):

$$\text{Amplitude} \propto \frac{N}{R^2} e^{-2k^2\sigma^2}$$

- Increasing N boosts amplitude at all k
- Increasing σ² damps amplitude at high k (strong k-dependence)
- The k-dependence difference marginally constrains them, but data must extend to
  high enough k (typically 12–14 Å⁻¹)
- **Best practice**: Use multiple k-weights (k¹, k², k³) to help separate

### R ↔ E₀ (typically r ≈ −0.3 to −0.5)

- The EXAFS phase: φ = 2kR + δ(k), with k = √(0.2625(E−E₀))
- Changing E₀ shifts the k-scale, which changes the apparent R (period ~π/2kmax)
- For Δk = 10 Å⁻¹ at kmax = 14: δE₀ of 1 eV shifts R by ~0.01 Å
- **Always float E₀ with tight bounds (±10 eV)** — fixing E₀ to 0 biases R

### Multi-Shell Deconvolution

When two shells are within ΔR ≤ 0.15 Å:
1. Their FT peaks overlap, making individual parameters highly correlated
2. Multiple k-weights help by changing the relative weighting
3. Constraints (e.g., CN₁ + CN₂ = known total CN) stabilize the fit

## Background Subtraction — The Fitting Impact

The autobk spline determines μ₀(E), which is subtracted to get χ(k). Key points:

- **Rbkg parameter** (typically 1.0 Å): Controls spline stiffness
  - Smaller Rbkg → more flexible spline → risk of removing low-R EXAFS
  - Larger Rbkg → stiffer spline → residual low-frequency in χ(k)
  - 1.0 Å is standard: removes components below typical first-shell distances
- **Spline k-range**: The spline is fit to χ(k) over the full k-range
- **Low-R artifact**: Check |χ(R)| for peaks below 1.0 Å — these are background
  subtraction artifacts, not real structure

## Feff File Format

feffNNNN.dat files from FEFF6/8 contain (after 13 header lines):
```
Column 0: k (Å⁻¹) — photoelectron wavenumber
Column 1: chi (or mag*sin(phase)) — EXAFS contribution from this path
Column 2: mag_feff — uncorrected backscattering amplitude |f(k)|
Column 3: pha_feff — uncorrected phase (includes central atom phase)
Column 4: red_fact — reduction factor
Column 5: lambda (Å) — mean free path
Column 6: real_pha — real part of phase (in newer versions)
```

**Critical**: Columns 2 and 3 need central-atom phase correction before use in the
EXAFS equation. FeffPathGroup._calc_chi applies this correction — using raw columns
directly introduces systematic phase errors (ΔE₀ drifts negative by 10–25 eV,
R-factors ~0.5).

## Reference: Standard Parameter Ranges

| Shell | R range (Å) | N range | σ² range (Å²) | ΔE₀ range (eV) |
|-------|-------------|---------|---------------|----------------|
| 1st M-O | 1.5–2.5 | 2–8 | 0.001–0.010 | ±15 |
| 1st M-S | 2.1–2.8 | 2–8 | 0.002–0.012 | ±15 |
| 2nd M-M | 2.5–4.0 | 1–12 | 0.002–0.020 | ±15 |
| 3rd | 3.5–5.5 | 2–24 | 0.003–0.025 | ±15 |

## Reference: Common Edge Energies for Calibration

| Element | K-edge (eV) | LIII-edge (eV) |
|---------|------------|----------------|
| Ti | 4966 | 456 |
| Cr | 5989 | 575 |
| Mn | 6539 | 640 |
| Fe | 7112 | 708 |
| Co | 7709 | 779 |
| Ni | 8333 | 855 |
| Cu | 8979 | 933 |
| Zn | 9659 | 1022 |
| Mo | 20000 | 2525 |
| W | 69525 | 10207 |

## References

1. Newville, M. "Fundamentals of XAFS" (2008), Consortium for Advanced Radiation
   Sources, University of Chicago.
2. Stern, E.A. and Heald, S.M. "Principles and Applications of EXAFS", in Handbook
   of Synchrotron Radiation (1983).
3. Koningsberger, D.C. and Prins, R. "X-ray Absorption: Principles, Applications,
   Techniques of EXAFS, SEXAFS, and XANES" (1988).
4. Rehr, J.J. and Albers, R.C. "Theoretical approaches to x-ray absorption fine
   structure", Rev. Mod. Phys. 72, 621 (2000).
