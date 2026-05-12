# XAFS Fitting Troubleshooting Guide

## Common Problems and Solutions

### 1. Fit Does Not Converge

**Symptoms**: `least_squares` returns success=False, parameters unchanged from initial values.

**Causes and solutions**:
- **Poor initial guesses**: Adjust initial parameter values closer to expected physical values
- **Too many free parameters**: Reduce N_var -- fix some parameters (e.g., fix S02, link sigma^2 values)
- **k-range inappropriate**: Try narrower k-range first (e.g., 3-10 instead of 3-14)
- **Bounds too tight**: Widen parameter bounds to give optimizer more room
- **Noisy data at high k**: Reduce k_max to exclude noisy region

### 2. Unphysical Parameter Values

**Symptoms**: N < 0, sigma^2 < 0, R values inconsistent with known structure.

**Solutions**:
- **Negative sigma^2**: Constrain sigma^2 >= 0.001; if it hits the bound, check if the path is real
- **N too large or small**: Check Feff degeneracy -- may have wrong path assignment
- **R systematically off**: Check E0 calibration; E0 error shifts all R values
- **Correlated N and sigma^2**: Fix one parameter or use constraints

### 3. Large R-factor (>0.1)

**Causes**:
- Missing important scattering paths
- Incomplete background subtraction
- Sample has multiple phases/species
- Data quality issues (noise, glitches)

**Diagnostic steps**:
1. Plot data and fit overlapped -- identify where fit deviates
2. Check residual -- systematic oscillations suggest missing paths
3. Try adding next shell paths
4. Check for beam damage or sample inhomogeneity

### 4. Missing Dependencies

**Symptom**: `ImportError: No module named 'scipy'`

**Solution**:
```bash
pip install numpy scipy matplotlib openpyxl
```

For Larch backend:
```bash
pip install xraylarch
```

### 5. LaTeX Rendering Issues in Figures

**Symptom**: Figures show raw LaTeX like `$S_0^2$` instead of formatted math.

**Solution**: matplotlib's built-in mathtext renderer is used by default (no external LaTeX needed).
If issues persist, check:
- matplotlib version >= 3.4
- Font configuration: `plt.rcParams['mathtext.default'] = 'regular'`

### 6. File Not Found Errors

**Symptom**: `FileNotFoundError: Data file not found`

**Check**:
- Use absolute paths or paths relative to the script execution directory
- On Windows, use forward slashes: `C:/Users/.../data.chi`
- Verify the file extension is supported (.chi, .dat, .txt, .csv)

### 7. Excel File Will Not Open

**Symptom**: Generated .xlsx file corrupted or unreadable.

**Check**:
- `openpyxl` version >= 3.0
- No special characters in sample name
- Output directory exists and is writable

## FAQ

**Q: How do I add more Feff paths?**
A: In the interactive session, tell the fitter to "add a path" and specify:
- Path name (e.g., "Mo-O2")
- Feff file reference
- Degeneracy
- Reff (from Feff calculation)
- Scattering atom type

**Q: Can I link parameters between paths?**
A: Yes. For example, link sigma^2 of similar paths:
- "Link sigma^2 of Mo-O1 and Mo-O2"
- Use the same parameter name for paths that share a value

**Q: How do I refit without losing previous results?**
A: Simply run the fit again. The Fit_XX folder auto-increments. All previous Fit_XX folders are preserved.

**Q: What if my data is in energy space (mu(E)) not k-space?**
A: The skill will prompt you about E0 and pre-edge ranges, then convert:
1. E -> k conversion: k = sqrt(2m_e(E - E0) / hbar^2)
2. Pre-edge subtraction
3. Normalization
4. Background subtraction -> chi(k)
