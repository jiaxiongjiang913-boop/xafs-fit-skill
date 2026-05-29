# XAFS Fitting Output Format Specification

## Directory Structure

```
project_dir/
├── data/                              # Original data files
├── scripts/
│   ├── 01_<sample>_XANES.py            # XANES normalization analysis
│   └── 02_<sample>_fit.py              # EXAFS fitting script
├── Fit/                                # All fitting results
│   ├── Fit_01/                         # First fit
│   │   ├── <sample>_fit.pdf            # 2-page PDF: Fig1 + Fig2+table
│   │   ├── <sample>_fit.png            # Figure only (no residual)
│   │   └── <sample>_fit_parameters.xlsx # 6-sheet Excel
│   ├── Fit_02/                         # Second fit
│   │   └── ...
│   └── Fit_03/                         # Third fit
│       └── ...
└── results/
    └── 02_<sample>_fit_report.txt      # Fitting report
```

## Key Rules

1. **Version control**: Each fit gets a new `Fit_XX` folder; old folders are never deleted
2. **Numbering**: Auto-increment (`Fit_01`, `Fit_02`, ...) based on existing folders
3. **File naming**: All files numbered to reflect processing order

## PDF Specification (2 pages)

### Page 1 - Fit Overview
- k-space figure: k^w * chi(k) vs k
- Data (black), Fit (red)
- **No residual**
- k-range window markers (green dotted lines)
- Text box with: sample name, R-factor, k-weight

### Page 2 - Fit Details
- Upper panel: |χ(R)| vs R, range 0–10 Å
  - Data (black), Fit (red)
  - **No residual**
  - R-range window markers (green dotted)
- Lower panel: Parameter table (text rendered with monospace font)
  - Fit Quality section (R-factor, chi^2_nu, N_indep, N_var)
  - Structure Parameters section (table with columns: Path, N, R, sigma^2, dE0)
  - Fit Conditions section (k-range, R-range, k-weight, window, S0^2)

## PNG Specification

- R-space figure: **|χ(R)|** vs R, range **0–10 Å**
- Data (black), Fit (red)
- **No residual subplot**
- **No parameter table**
- Fit parameters shown as text annotation in corner (small monospace font)
- Clean figure suitable for publication/presentation

### Fit Figure Specification (2-row layout)

**Upper panel: k-space**
- k^w·χ(k) vs k
- Data (black), Fit (red)
- **No residual**
- k-range window markers (green dotted)
- Text box: sample name, R-factor, k-weight

**Lower panel: R-space |χ(R)|, 0–10 Å**
- |χ(R)| vs R, full 0–10 Å range
- Data (black), Fit (red)
- **No residual**
- R-range window markers (green dotted)
- Parameter annotation (small text): CN, R, σ², ΔE₀ per shell

## LaTeX Math Formatting

All figures must use proper math formatting:
- `$S_0^2$` = S₀²
- `$\sigma^2$` = σ²
- `$\chi^2_\nu$` = χ²_ν
- `$\AA^{-1}$` = Å⁻¹
- `$\AA$` = Å
- `$k$` = k
- `$R$` = R

Use matplotlib's built-in mathtext renderer (no external LaTeX needed).

## Excel File Specification

### Sheet 1: Feff_Paths
| Path Name | Feff File | Degeneracy | Reff (A) | Scattering Atoms | Shell |
|-----------|-----------|------------|----------|-----------------|-------|
| Mo-O      | feff0001  | 2.0        | 1.70     | O               | 1st   |

### Sheet 2: Fit_Parameters
| Parameter | Initial Value | Lower Bound | Upper Bound | Fit Value | Uncertainty | Fixed |
|-----------|--------------|-------------|-------------|-----------|-------------|-------|
| N_Mo-O    | 2.0          | 0.5         | 8           | 2.1       | 0.3         | No    |

### Sheet 3: Amplitude_Expression
| Property | Value |
|----------|-------|
| S02      | 0.9   |
| S02 Status | Fixed |

### Sheet 4: Fit_Conditions
| Condition | Value |
|-----------|-------|
| k-range (A^-1) | 3.0 - 12.0 |
| R-range (A) | 1.0 - 5.0 |
| k-weight | 2 |

### Sheet 5: Data_Processing
| Step | Description |
|------|-------------|
| 1    | Loaded data from sample.chi |

### Sheet 6: Results
| Parameter | Value | Uncertainty | Unit |
|-----------|-------|-------------|------|
| R_Mo-O    | 1.70  | 0.01        | Angstrom |

## Fitting Report Format

```
XAFS FIT REPORT
Sample: <sample_name>
Fit number: <XX>
Date: YYYY-MM-DD

FIT QUALITY
  R-factor:       0.XXXX
  Reduced chi-sq: X.XX
  N_indep:        XX
  N_var:          XX

STRUCTURE PARAMETERS
  Path        N       R(A)      sigma^2(A^2)    DeltaE0(eV)
  ---------------------------------------------------------
  Mo-O       X.X     X.XX      0.00XX          X.X
  Mo-Mo      X.X     X.XX      0.00XX          X.X

FIT CONDITIONS
  k-range:    X - XX Ang^-1
  R-range:    X - XX Ang
  k-weight:   X
  S02:        X.XX (fixed)
  Window:     Hanning, dk=1.0

DATA PROCESSING
  1. E0 calibration at XXXX eV
  2. Pre-edge subtraction (linear, -150 to -30 eV)
  3. Normalization (polynomial, 150 to 800 eV)
  4. Background removal (AUTOBK, Rbkg=1.0 Ang)
  5. k-weight = X
  6. FT window: [X, XX] Ang^-1
```
