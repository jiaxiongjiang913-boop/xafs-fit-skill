# XAFS Fitting Troubleshooting Guide

## 1. Fit Does Not Converge

**Symptoms**: `least_squares` returns success=False, parameters unchanged.

**Root causes (ordered by frequency)**:

### 1a. Poor initial parameter guesses
- R: Start at the Feff Reff value (from paths.dat); set delr = 0.0 initially
- σ²: Start at 0.003–0.005 for first shell, 0.005–0.010 for higher shells
- CN: Start at Feff degeneracy or a physically reasonable value
- ΔE₀: Start at 0.0; allow ±10–15 eV variation
- **Diagnostic**: Check if the optimizer immediately hits bounds — this means initial
  values are far from the minimum

### 1b. Over-parameterization
- Count N_var vs N_indep = 2·Δk·ΔR/π
- Fix non-critical parameters (e.g., fix σ² for clearly ordered shells, link σ² of
  similar paths)
- **Diagnostic**: Try fitting with fewer free variables; if convergence improves,
  the model was over-parameterized

### 1c. k-range inappropriate
- Start with narrower k-range (e.g., 3–10 Å⁻¹ instead of 3–14 Å⁻¹)
- High-k noise (low signal-to-noise above 12–14 Å⁻¹) can derail optimizer
- Expand k-range only after convergence at narrower range

### 1d. Background subtraction artifacts
- If |χ(R)| shows peaks below 1.0 Å, the background spline is too flexible
- Increase Rbkg (e.g., from 0.8 to 1.0 or 1.2)

## 2. Unphysical Parameter Values

### 2a. Negative σ²

**Physics**: σ² is the mean-square relative displacement — a variance, which cannot
be negative. A fitted σ² at zero or negative indicates:
1. **Path is not real**: The signal attributed to this path does not exist in the data
   → Remove the path from the model
2. **R is wrong**: If R is offset by >0.1 Å from the true value, σ² may compensate
   → Re-examine the Feff R_res and check possible bond distances
3. **Wrong scatterer Z**: If the Feff calculation used the wrong atom type, both
   amplitude and phase will be wrong → Check Feff input
4. **Constraint violation**: σ² at the lower bound (0.001) → verify the path is needed

### 2b. CN inconsistent with known structure

- For crystalline systems, CN must be integer (within error)
- For amorphous systems, non-integer CN reflects structural disorder
- CN_short + CN_long should equal the total CN expected from coordination chemistry
- **a-MoO3 example**: CN_total = 5.0, consistent with distorted octahedral MoO₆
  in amorphous MoO₃ (some O at >2.5 Å are outside the fitting window)

### 2c. R systematically offset

- If all R values are offset by the same amount: E₀ calibration error
  → ΔE₀ will absorb this — large |ΔE₀| (>10 eV) with good R means the calibration
  shift was applied correctly but Feff's muffin-tin E₀ doesn't match
- If only one R is offset: that shell assignment is wrong, or two shells are merging
  into one average distance

### 2d. ΔE₀ too large (>|15| eV)

- **Meaning**: ΔE₀ absorbs ALL systematic energy offsets:
  - Experimental calibration error (~0.5–2 eV at modern beamlines)
  - Feff muffin-tin zero error (can be 5–10 eV depending on bonding)
  - Chemical shift from reference (edges shift with oxidation state)
- |ΔE₀| > 15 eV almost always means:
  - Missing central-atom phase correction (raw feff columns used instead of _calc_chi)
  - Wrong structural model (wrong phase, neighbor Z, or geometry)
  - Data was not properly energy-calibrated
- **When all paths share E₀**: a single E₀ absorbing a systematic shift is fine;
  large E₀ with good fit quality is not inherently wrong — it's absorbing Feff's
  systematic error
- **When paths have independent E₀**: large differences between path E₀ values
  indicate structural misassignment

## 3. Large R-factor (>0.1)

### Diagnostic Protocol

1. **Plot χ(k) data vs fit overlapped** → identify k-regions where fit deviates
2. **Examine residual in k-space** → systematic (not random) oscillations mean
   missing frequency components = missing shells
3. **Plot χ(R) data vs fit with residual** → identify R-regions where fit fails
4. **Check |χ(R)| for unexplained peaks** → add paths for those peaks

### Common causes by R-factor range:

| R-factor | Likely Issue |
|----------|-------------|
| 0.05–0.10 | Minor: N_var near N_indep limit, slight model incompleteness |
| 0.10–0.20 | Missing one significant path OR poor background subtraction |
| 0.20–0.50 | Missing major shell (second shell entirely absent) OR wrong scatterer Z |
| >0.50 | Fundamental model error: wrong phase (no central-atom correction), wrong structure |

### Corrective actions:
1. Add next coordination shell paths
2. Check for multiple-scattering contributions (especially collinear geometries)
3. Re-examine the Feff input structure — wrong lattice parameters or space group
4. Verify data quality: beam damage, sample inhomogeneity, self-absorption

## 4. Systematic Oscillations in Residual

**Symptom**: The residual χ_residual(k) shows periodic oscillations, not random noise.

**Root cause**: The fit model is missing a frequency component (i.e., a scattering path).

**Diagnostic procedure**:
1. Fourier transform the residual: FT[χ_residual] → identify R of missing peak
2. Check Feff paths.dat — look for paths at that R with significant amplitude
3. Add the identified path to the fit model
4. If no path exists at that R, reconsider the structural model

**Example**: In the a-MoO3 project, the first-shell fit (Mo-O only) showed systematic
high-frequency oscillations in the residual because the Mo-Mo shell at ~3.5 Å was
not included.

## 5. CN/σ² Anti-Correlation (r ≈ −0.90)

**Physics**: Both CN and σ² affect the EXAFS envelope amplitude. Increasing CN
boosts the signal at all k; increasing σ² damps it more at high k.

**When it becomes problematic**:
- Δk is short (kmax < 12 Å⁻¹): the k-dependence difference is insufficient to
  separate CN from σ² → both parameters are poorly determined
- CN and σ² have >95% correlation in the covariance matrix

**Mitigation strategies** (in order of preference):
1. Extend kmax to ≥13–14 Å⁻¹ (if data quality permits)
2. Fix σ² to a known value from a model compound or literature
3. Link σ² values of similar shells (e.g., same σ² for Mo-O_short and Mo-O_long)
4. Use multiple k-weights (fit simultaneously with k¹, k², k³)
5. Fix CN to crystallographic value and float only σ² and R

## 6. R/E₀ Correlation

**Physics**: E₀ changes the k-scale, which shifts the EXAFS phase. The EXAFS phase
is 2kR + δ(k) — changing both E₀ (via k) and R affects the phase similarly for a
single shell. This is why E₀ and R are correlated.

**Typical correlation strength**: r ≈ −0.3 to −0.5 (weaker than CN/σ², but present)

**Mitigation**:
- Always float E₀ — fixing it to 0 biases R by 0.01–0.03 Å
- Use a single E₀ for ALL paths from the same absorber (this is physically correct)
- Tight E₀ bounds (±10 eV) prevent wild values
- Evaluate: if ΔE₀ and ΔR both converge to physically reasonable values, the
  correlation is not problematic

## 7. Background Subtraction Issues

### Symptoms in |χ(R)|:

| Artifact | Cause | Fix |
|----------|-------|-----|
| Peak at 0.5–1.0 Å | Spline too flexible (Rbkg too small) | Increase Rbkg to 1.0–1.2 |
| Rising baseline < 1 Å | Residual low-R from over-subtraction | Decrease Rbkg |
| False peak at 0 Å | DC offset / normalization error | Check edge step normalization |
| Overall too smooth | Spline removed EXAFS signal! | Decrease Rbkg, check spline k-range |

**The Rbkg rule**: Rbkg should be ~0.5 Å less than the shortest expected bond
distance. For metal oxides with M-O at ~1.5–2.0 Å, Rbkg = 1.0 is standard.

## 8. Fourier Transform Artifacts

### Side-lobes / ringing
- Caused by sharp window cutoffs at kmin or kmax
- Use Hanning or Kaiser-Bessel window with dk ≥ 1 Å⁻¹
- Wider dk reduces ringing but also reduces R-resolution

### Peak splitting
- Truncation ripples from finite k-range can create apparent peak splitting
- Check: does splitting persist with different k-ranges? If not, it's a truncation artifact
- Use dk ≥ 1.5 to suppress

### R-axis shift
- |χ(R)| peaks are phase-uncorrected — they appear ~0.3–0.5 Å shorter than true R
- This is NOT an artifact — it's the δ(k) phase shift
- During fitting with Feff phases included, fitted R values are TRUE distances

## 9. Self-Absorption Artifacts (Fluorescence Data)

**Symptom**: EXAFS oscillations appear damped or absent, especially at the white line.

**Physics**: For concentrated samples measured in fluorescence, μ(E) variations change
the penetration depth, causing the fluorescence yield to saturate.

**Detection**:
- Compare fluorescence and transmission data (if available)
- Check edge jump: if Δμt > 1 in transmission, fluorescence will have self-absorption

**Correction**: Apply the Booth-Bridges self-absorption correction algorithm (available
in Athena/Larch).

## 10. Dead Time Effects (Fluorescence Detectors)

**Symptom**: Signal non-linearity — EXAFS amplitude appears compressed, especially
at high count rates (>10⁵ Hz per detector element).

**Detection**: Plot I_f/I_0 vs I_f — should be linear. Saturation bends the curve down.

**Fix**:
- Reduce incident flux (attenuate beam, defocus)
- Use more detector elements in parallel
- Apply dead-time correction: I_true = I_measured / (1 − τ × I_measured)
  where τ is the detector dead time (~3–10 μs)

## 11. Missing Dependencies

**Symptom**: `ImportError: No module named 'scipy'`

```bash
pip install numpy scipy matplotlib openpyxl
```

For Larch backend:
```bash
pip install xraylarch
```

## 12. LaTeX Rendering Issues

**Symptom**: Figures show raw LaTeX, not formatted math.

**Solution**: matplotlib's built-in mathtext renderer is used by default.
No external LaTeX installation is needed. If problems persist:
- Ensure matplotlib ≥ 3.4
- Set `plt.rcParams['mathtext.default'] = 'regular'`
- Use PGF backend only if full LaTeX installation is available

## 13. File Not Found

- Use absolute paths or relative to script directory
- Windows: forward slashes (`C:/Users/...`)
- Verify file extension matches expected format

## Fit Diagnosis Checklist

Before accepting any fit result, verify:

- [ ] R-factor < 0.05 (or < 0.10 with explanation)
- [ ] N_var < N_indep (preferably ≤ 2/3 × N_indep)
- [ ] All CN ≥ 0 and physically plausible
- [ ] All σ² > 0 (not at lower bound)
- [ ] All ΔR within ±0.15 Å of Feff Reff
- [ ] |ΔE₀| < 10–15 eV (or explained)
- [ ] Residual looks like noise (no systematic oscillations)
- [ ] Parameters not at bounds (if at bound, widen bound or reconsider)
- [ ] Correlations between parameters < 0.95 (except CN/σ² which is expected)
- [ ] χ²_ν ≈ 1 (very low suggests over-fitting or overestimated noise)
- [ ] Fitted R values match expected bond distances from crystal chemistry

## References

1. Newville, M. "Fundamentals of XAFS" (2008), Chapter 6: XAFS Data Modeling.
2. Stern, E.A. "Number of relevant independent points in x-ray-absorption
   fine-structure spectra", Phys. Rev. B 48, 9825 (1993).
3. Booth, C.H. and Bridges, F. "Improved self-absorption correction for
   fluorescence measurements of extended x-ray absorption fine-structure",
   Phys. Scr. T115, 202 (2005).
