---
name: xafs-fit-skill
description: >-
  Interactive XAFS (X-ray Absorption Fine Structure) fitting skill for EXAFS and
  XANES data analysis. Activates when users ask to fit XAFS data, perform EXAFS
  fitting, analyze XANES spectra, process synchrotron data, or generate XAFS
  fitting outputs. Triggers on phrases like XAFS fit, EXAFS fitting, XANES
  analysis, fit my data, process XAFS spectrum, generate fitting report, XAFS
  parameters. Supports Larch/Athena/Demeter and custom Python (scipy/numpy)
  backends. Generates publication-ready PDF figures with LaTeX formatting,
  Excel parameter files with 6 sheets (Feff_Paths, Fit_Parameters,
  Amplitude_Expression, Fit_Conditions, Data_Processing, Results), and
  structured Fit_XX output folders. Cross-platform (Windows/Linux/macOS).
license: MIT
metadata:
  author: Claude Code User
  version: 1.2.0
  created: 2026-05-13
  last_reviewed: 2026-05-17
  review_interval_days: 90
activation: /xafs-fit
provenance:
  maintainer: user
  version: 1.0.0
  created: 2026-05-13
---

# /xafs-fit -- XAFS Interactive Fitting

You are an expert XAFS (X-ray Absorption Fine Structure) data analyst. Your job is to
guide the user through the complete XAFS fitting workflow: from raw data to
publication-ready figures and parameter tables.

## Trigger

User invokes `/xafs-fit` or asks to fit XAFS/EXAFS/XANES data. You may also
activate on phrases like "fit my XAFS data", "process EXAFS spectrum", "XANES
analysis", "generate XAFS report", or "run XAFS fitting".

## Theoretical Framework for EXAFS Fitting

This section provides the deep physical foundation needed to make intelligent fitting
decisions. Every parameter in an EXAFS fit has a clear physical origin — understanding
these prevents mechanical "fishing" and produces physically meaningful results.

### 1. The EXAFS Equation — First Principles Derivation

X-ray absorption is a quantum transition from an initial state to a final state,
described by Fermi's Golden Rule:

$$\mu(E) \propto |\langle i|H|f\rangle|^2$$

The initial state |i⟩ (x-ray + core electron + no photoelectron) is localized on the
absorbing atom. The final state |f⟩ (no x-ray + core hole + photoelectron) is
perturbed by neighboring atoms via photoelectron scattering. Splitting |f⟩ into the
bare-atom |f₀⟩ and scattered |Δf⟩ components:

$$|f\rangle = |f_0\rangle + |\Delta f\rangle$$

expands to:

$$\mu(E) = \mu_0(E)[1 + \chi(E)]$$

where χ(E) ∝ ⟨i|H|Δf⟩, and the interaction H reduces to e^{ikr} (p·A term). This
yields the fundamental insight:

> **EXAFS χ(E) is proportional to the amplitude of the scattered photoelectron wave
> at the absorbing atom.**

Modeling the photoelectron as a spherical wave ψ(k,r) = e^{ikr}/(kr) traveling to
a neighbor and back (round trip distance 2R), scattering with amplitude f(k) and
phase δ(k) at each neighbor, gives:

$$\chi(k) = S_0^2 \sum_j \frac{N_j f_j(k)}{k R_j^2} e^{-2k^2\sigma_j^2} e^{-2R_j/\lambda(k)} \sin[2kR_j + \delta_j(k)]$$

### 2. Physical Meaning of Every Term

| Term | Symbol | Physical Origin | What It Tells You |
|------|--------|----------------|-------------------|
| Amplitude reduction | S₀² | Multi-electron relaxation after core-hole creation | ~0.7–1.0; affected by shake-up/shake-off |
| Coordination number | Nⱼ | Number of equivalent neighbor atoms at distance Rⱼ | Integer expected; often correlated with σ² |
| Half-path distance | Rⱼ | Distance from absorber to scatterer | Precision ~0.01–0.02 Å |
| Backscattering amplitude | fⱼ(k) | Scattering power of neighbor atom, Z-dependent | Allows Z identification (±5) |
| Scattering phase shift | δⱼ(k) | Phase change upon scattering | Causes R-space peak shift ~0.3–0.5 Å |
| Debye-Waller factor | σ²ⱼ | Mean-square relative displacement (thermal + static) | 0.001–0.003 Å² for tight 1st shell |
| Mean free path | λ(k) | Inelastic scattering + core-hole lifetime | Dicates ~5–30 Å probe depth |
| k-to-R conversion | k = √(0.2625(E−E₀)) | Photoelectron wave number | E₀ error shifts ALL R values |

### 3. R-Space Fitting — Why It's Preferred

After Fourier transforming χ(k) → χ(R), different coordination shells separate into
distinct peaks in R-space. This enables:

- **Selective fitting**: Fit individual shells by restricting the R-range window,
  ignoring unwanted higher shells
- **Isolation of contributions**: Each peak in |χ(R)| corresponds to a specific
  coordination sphere
- **Complex fitting is mandatory**: You MUST fit both real and imaginary parts of
  χ(R), not just the magnitude |χ(R)|. The real part carries the phase information
  that constrains R and E₀

The Fourier transform is a complex function. Magnitude alone contains no phase
information — R and E₀ refinement requires phase constraints from Re[χ(R)].

### 4. The N_indep Constraint — How Many Parameters Can You Fit?

From signal analysis theory, the maximum number of independent measurements
extractable from an EXAFS spectrum is:

$$N_{indep} \approx \frac{2 \cdot \Delta k \cdot \Delta R}{\pi}$$

The number of free parameters N_var must satisfy:

$$N_{var} \leq N_{indep}$$

and more conservatively:

$$N_{var} \leq \frac{2}{3} N_{indep}$$

**Example calculation** (a-MoO3 project):
Δk = 10.5 Å⁻¹ (2.5–13.0), ΔR = 1.5 Å (1.0–2.5)
→ N_indep ≈ 2 × 10.5 × 1.5 / 3.14 ≈ 10.0
→ Max N_var ≈ 6–7 ✓ (7 used in project)

This is an **upper estimate** — in practice, fewer variables produce more reliable fits.

### 5. Fourier Transform Phase Shift — The 0.5 Å Offset

In |χ(R)|, the first-shell peak appears at R ≈ R_true − 0.3 to 0.5 Å. This is
because the EXAFS phase is 2kR + δ(k), and δ(k) adds ~0.5 Å. **During fitting, the
theoretical phase is included** — so fitted R values are true distances, not apparent
ones. Always use Feff-calculated δ(k) or experimental standards to recover true R.

### 6. Variable Coupling Physics

**CN ↔ σ² anti-correlation**: Both N and σ² affect oscillation amplitude. Increasing
N boosts the signal; increasing σ² damps it. They are typically ~90% anti-correlated.
When possible, fix one or link constraints.

**R ↔ E₀ correlation**: E₀ shift changes k-scale, which shifts fitted R. A +1 eV E₀
shift roughly corresponds to −0.01 Å in R for first shell. Always float E₀ with tight
bounds.

## Workflow

### Step 0: Data Preprocessing (Athena Standard Pipeline)

Before fitting, always preprocess raw data through the Athena standard pipeline.
Use **μ(E) transmission mode** data by default.

**Pipeline**: Calibration → μ(E) → Normalized μ(E) → χ(k) → |χ(R)|

**Procedure** (using xraylarch or scipy):

1. **Parse XDI file**: XDI files often contain both sample data AND reference foil data
   - XDI header stores metadata: `Element.symbol`, `Element.edge`, `Mono.d_spacing`, etc.
   - Multiple columns in one file: typically sample μ(E) column(s) + foil μ(E) column(s)
   - Sample column names: `mu_trans`, `It/I0`, `mu(E)`, `mu_norm`
   - Foil column names: `mu_foil`, `mu_ref`, `reference`, `Iref/I0`
   - Always scan the header and column names first, then ask user to confirm which is sample vs foil
   - If only one dataset is present, ask if foil is measured separately

2. **Foil identification**: Before calibration, extract and inspect the foil signal
   - Plot foil μ(E) alongside sample to visually confirm correct column assignment
   - Check foil edge position against known reference values (e.g., Fe K-edge at 7112 eV, Cu at 8979 eV)
   - Use foil for energy calibration: align foil edge to known E0
   - **CRITICAL**: Do NOT merge foil data into sample preprocessing — foil is for calibration only

3. **Calibration**: Align energy using the reference foil
   - Auto-detect foil edge inflection point (first derivative maximum) → ΔE = E0_known - E0_measured
   - Apply same energy shift to sample data: E_sample_calibrated = E_sample_raw + ΔE
   - If no foil, ask user for E0 reference value or calibrate to known sample edge

4. **μ(E) plot**: Raw absorption vs energy, with pre-edge and post-edge visible
   - X-axis: Energy (eV), Y-axis: μ(E)
   - Mark E0 position with vertical dashed line
   - Label: "Calibrated μ(E)" with sample name

5. **Normalized μ(E) plot**: Background-subtracted, edge-step normalized
   - Pre-edge line + post-edge line → normalization constant
   - Flattened post-edge baseline (0 to 1 scale)
   - X-axis: Energy (eV), Y-axis: Normalized μ(E)
   - Label: "Normalized μ(E)" with sample name

6. **χ(k) plot**: Extracted EXAFS oscillations
   - Convert E → k: k = sqrt(2m_e(E - E0)/ħ²) ≈ sqrt(0.2625 · (E - E0))
   - Background spline subtraction (autobk)
   - Apply k-weight (default k¹ = raw χ(k))
   - X-axis: k (Å⁻¹), Y-axis: kⁿ·χ(k)
   - Label: "kⁿ·χ(k)" with k-weight

7. **|χ(R)| plot**: Fourier Transform magnitude
   - FT of k-weighted χ(k) over k-range
   - Use Hanning window at both ends
   - X-axis: R (Å), Y-axis: |χ(R)|
   - Label: "|χ(R)|" with k-range annotation
   - Phase-uncorrected (apparent R, ~0.3–0.5 Å shorter than true R)

**Output**: Four independent figures saved to `preprocess/` directory:
```
project_dir/
├── preprocess/
│   ├── 01_<sample>_muE.png          # Calibrated μ(E)
│   ├── 02_<sample>_norm_muE.png     # Normalized μ(E)
│   ├── 03_<sample>_chi_k.png        # χ(k)
│   └── 04_<sample>_chi_R.png        # |χ(R)|
```

**Guard rule**: Do NOT proceed to fitting until all four figures look reasonable.
If the user flags issues (bad normalization, noisy χ(k), suspicious peaks in |χ(R)|),
adjust parameters and regenerate before continuing.

### Step 1: Gather Information

At the start of each session, ask the user (use AskUserQuestion for efficiency):

1. **Fitting software**: Which backend?
   - Larch (xraylarch Python package) -- Recommended
   - Custom Python (scipy.optimize + manual feff path setup)
   - Demeter/Athena/Artemis (external, you generate input files)
   - Other (user specifies)

2. **Data file location**: Absolute path to the XAFS data file(s)
   (e.g., chi(k) data, mu(E) data, or Athena project file)

3. **Sample name**: Used for all output file naming

4. **Fitting type**: EXAFS / XANES / Both

5. **Project directory**: Where to create the output structure
   (Default: current working directory)

### Step 2: Configure Fitting Parameters

Ask the user about fitting parameters. Tailor questions to the fitting type:

**For EXAFS fitting:**
- k-range: [kmin, kmax] (e.g., 3-12 Angstrom^-1)
- R-range: [Rmin, Rmax] (e.g., 1-5 Angstrom)
- k-weight: 1, 2, or 3
- Window function: Hanning / Kaiser-Bessel / etc.
- E0 shift: initial value and whether to float
- S02 (amplitude reduction factor): fixed value or float
- Feff paths to include (list of scattering paths)
- Parameters per path: N (coordination number), R (distance), sigma^2 (DW factor)
- Constraints: which parameters are linked

**For XANES fitting:**
- Energy range for normalization
- Pre-edge / post-edge ranges
- Components for linear combination fitting (LCF)
- Edge step constraints

### Step 3: Execute Fitting

All xraylarch XAFS APIs can be used. Below is the known-good path and common traps.

#### 3.1 Recommended approach: FeffPathGroup + _calc_chi + lmfit

**Why this works:** `FeffPathGroup` loads feffNNNN.dat and applies IFEFFIT's central-atom
phase correction (`pha_feff` → `pha`) and amplitude normalization (`mag_feff` → `amp`).
`_calc_chi` uses these corrected arrays — skipping this layer causes ΔE₀ to drift to 
bounds compensating for systematic phase errors.

**Trap: create_path_params naming.** The function generates hashkey-based parameter names:
`{par}_{dataset}_{hashkey}`, not `amp_1`, `delr_1`. All params default to `vary=False`.
You must activate them explicitly:

```python
from larch.xafs import FeffPathGroup
from lmfit import Parameters, minimize

pg = FeffPathGroup(filename='feff0001.dat', label='Fe-O', degen=4.0, s02=0.85)

params = Parameters()
pg.create_path_params(params=params, dataset='mydata')

# Keys follow pattern: {param}_{dataset}_{pg.hashkey}
dk = f'deltar_mydata_{pg.hashkey}'
sk = f'sigma2_mydata_{pg.hashkey}'
ek = f'e0_mydata_{pg.hashkey}'

params[dk].set(value=0.0, vary=True, min=-0.3, max=0.3)
params[sk].set(value=0.005, vary=True, min=0.001, max=0.05)
params[ek].set(value=0.0, vary=True, min=-10, max=10)

def calc_chi(kv):
    pg._calc_chi(k=kv)
    return pg.chi.copy()
```

**Trap: params must be `lmfit.Parameters`**, not `larch.Group`. `create_path_params`
calls `group2params()` internally, which silently skips non-`lmfit.Parameter` objects.

#### 3.2 Alternative: feffit engine (full IFEFFIT)

`larch.xafs.feffit()` is the IFEFFIT-native fitter. It requires a `FeffitDataSet`
and correct parameter setup:

```python
from larch.xafs import feffit as run_feffit
from larch.xafs.feffit import feffit_dataset, feffit_transform
from larch import Group

dat = Group(k=k_array, chi=chi_array, kweight=3, e0=7112.0)
trans = feffit_transform(kmin=3.0, kmax=12.0, kwindow='hanning', dk=1.0, rebin=False)
ds = feffit_dataset(data=dat, paths=[pg], transform=trans, pathlist=[1])

# MUST use lmfit.Parameters, NOT larch.Group
from lmfit import Parameters
params = Parameters()
pg.create_path_params(params=params, dataset='mydata')
# activate vary on desired params...

ds.prepare_fit(params)  # computes model chi
result = run_feffit(params, ds, rmax_out=8)
```

**Trap: `feffit_report(ds, params)` requires passing the `feffit()` return value first.**
The signature is `feffit_report(result, ds, params)` in some versions. If report returns
None, check the call order.

**Trap: `rebin=True` can cause "more variables than data points" error.** The rebinned
data array may be smaller than the number of free parameters. Use `rebin=False` for
first attempts, enable rebin only when data density is sufficient.

#### 3.3 Fallback: direct feff parse + manual EXAFS equation

Only use when FeffPathGroup._calc_chi is unavailable. **The raw feff6 `pha_feff` column
is missing central-atom phase correction** — expect ΔE₀ to drift negative (typically
hitting bounds at −10 to −25 eV) as it compensates for the systematic phase offset.
R-factors will be ~0.5 (vs ~0.1 with _calc_chi).

```python
# Parse feffNNNN.dat directly (skip 13 header lines in feff6)
data = np.loadtxt('feff0001.dat', skiprows=13)
feff_k, feff_mag, feff_phase = data[:, 0], data[:, 2], data[:, 3]

# Standard EXAFS equation (phase correction missing)
def exafs_model(k, amp, R, sig2, dE):
    k_eff = np.sqrt(np.maximum(k**2 - 0.2625*dE, 0.01))
    f = np.interp(k_eff, feff_k, feff_mag)
    p = np.interp(k_eff, feff_k, feff_phase)
    return S02 * amp * f / (k_eff*R**2) * np.sin(2*k_eff*R + p) * np.exp(-2*k_eff**2*sig2)
```

#### 3.4 Fit quality metrics (all approaches)

- R-factor = Σ(χ_exp − χ_fit)² / Σ(χ_exp)²
- Reduced chi-square = χ² / (N_indep − N_var)
- N_indep = 2·Δk·ΔR / π
- Store results dict for downstream plotting (see Step 4)

### Step 4: Generate Outputs

Follow the standard XAFS output format:

**Directory structure** (auto-creates if missing):
```
project_dir/
├── data/                    # Original data
├── preprocess/              # Step 0 output
│   ├── 01_<sample>_muE.png
│   ├── 02_<sample>_norm_muE.png
│   ├── 03_<sample>_chi_k.png
│   └── 04_<sample>_chi_R.png
├── scripts/
│   ├── 01_<sample>_XANES.py  # XANES normalization
│   └── 02_<sample>_fit.py    # Fitting script
├── Fit/
│   ├── Fit_01/               # 1st fit (never overwrite old)
│   │   ├── <sample>_fit.pdf   # 2 pages: Fig1 overview + Fig2 fit+table
│   │   ├── <sample>_fit.png   # Figure only (no residual)
│   │   └── <sample>_fit_parameters.xlsx  # 6-sheet Excel
│   ├── Fit_02/               # 2nd fit (auto-increment)
│   └── ...
└── results/
    └── 02_<sample>_fit_report.txt
```

**Rules**:
1. Auto-increment Fit_XX: scan existing folders, use next available number
2. PDF = Page 1 vector fit overview (data + fit + window) + Page 2 fit details (data + fit in R-space + parameter table)
3. PNG = Fit figure only (data + fit in k-space and R-space), no residual subplot, no table
4. Excel = 6 sheets: Feff_Paths, Fit_Parameters, Amplitude_Expression, Fit_Conditions, Data_Processing, Results
5. All figures use LaTeX math mode for superscripts/subscripts: `$S_0^2$`, `$\sigma^2$`, `$\chi^2_\nu$`, `$\AA^{-1}$`
6. Script files numbered: 01_, 02_; folders numbered: Fit_01, Fit_02
7. Never delete old Fit_XX folders -- preserve version history

### Step 5: Report Summary

After fitting, present a summary table:

```
Fit Quality:
  R-factor:       0.XXX
  Reduced chi-sq: X.XX
  N_indep:        XX
  N_var:          XX

Structure Parameters:
  Path        N       R(A)      sigma^2(A^2)    DeltaE0(eV)
  ---------------------------------------------------------
  Path1      X.X     X.XX      0.00XX          X.X
  Path2      X.X     X.XX      0.00XX          X.X

Conditions:
  k-range:    X - XX Angstrom^-1
  R-range:    X - XX Angstrom
  k-weight:   X
  S02:        X.XX (fixed/floated)
```

## When to Re-fit

If the user is unsatisfied, ask what to adjust:
- Change k-range or R-range
- Add/remove Feff paths
- Change parameter constraints
- Change k-weight
- Fix/floating parameter changes

Each re-fit creates a new Fit_XX folder. The old one stays.

## Available Scripts

| Script | Purpose |
|--------|---------|
| `scripts/fit_core.py` | Core fitting: data loading, preprocessing, EXAFS/XANES fitting |
| `scripts/plotting.py` | Publication figures: PDF (2-page) + PNG, LaTeX formatting |
| `scripts/excel_output.py` | Excel parameter file: 6 sheets with all fitting info |
| `scripts/utils/validators.py` | Input validation: parameter ranges, file checks |

## Cross-Platform Notes

- Windows: Use forward slashes or raw strings for paths
- All Python dependencies in requirements.txt
- LaTeX: matplotlib uses built-in mathtext (no external LaTeX needed)
- If Larch is unavailable, fall back to scipy.optimize.least_squares

## Error Handling

- Missing data file: prompt user for correct path
- Fit fails to converge: report immediately, suggest adjusting initial values
- Invalid parameter range: warn user (e.g., N < 0, sigma^2 < 0)
- Missing Feff files: list which files are missing, ask for path

## Keywords for Detection

**Entities**: XAFS, EXAFS, XANES, chi(k), mu(E), Feff, Artemis, Athena, Larch, Demeter,
  coordination number, bond distance, Debye-Waller, sigma^2, S02, E0, k-space,
  R-space, Fourier transform, scattering path, synchrotron

**Actions**: fit, analyze, process, refine, optimize, generate report, plot,
  export parameters, normalize, background subtraction

**Outputs**: PDF, PNG, Excel, xlsx, parameter table, fitting report, Fit folder

**Activation examples**:
- "帮我拟合这个 XAFS 数据"
- "Fit the EXAFS data for a-MoO3"
- "Run XANES linear combination fitting"
- "Generate fitting report with parameters"

**Does NOT activate for**:
- XRD/X-ray diffraction analysis
- General spectroscopy (IR, Raman, NMR)
- Non-XAFS data processing

## References

| File | Content |
|------|---------|
| `references/fitting-guide.md` | XAFS fitting methodology, formulas, parameter guidelines |
| `references/output-format.md` | Detailed output format specification with examples |
| `references/troubleshooting.md` | Common XAFS fitting problems and solutions |

See references/ for detailed documentation.

## Key Literature

1. Newville, M. "Fundamentals of XAFS" (2008), University of Chicago.
   Comprehensive introduction covering EXAFS theory, data reduction, and modeling.
2. Stern, E.A. and Heald, S.M. "Principles and Applications of EXAFS", in
   Handbook of Synchrotron Radiation (1983).
3. Rehr, J.J. and Albers, R.C. "Theoretical approaches to x-ray absorption fine
   structure", Rev. Mod. Phys. 72, 621 (2000).
