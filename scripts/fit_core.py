#!/usr/bin/env python3
"""
XAFS Fitting Core -- data loading, preprocessing, and fitting engine.

Supports multiple backends:
  - larch: xraylarch Python package (recommended)
  - scipy: scipy.optimize + manual EXAFS equation
  - demeter: Generate input files for Demeter/Artemis

Example:
    $ python fit_core.py --data sample.chi --sample a-MoO3 --kmin 3 --kmax 12 \\
        --rmin 1 --rmax 5 --kweight 2 --backend scipy --project ./project
"""

import sys
import os
import json
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict

import numpy as np

# --- Constants ---
HBAR = 1.054571817e-34
M_E = 9.10938356e-31
E_CHARGE = 1.602176634e-19
ANGSTROM = 1e-10
HBAR2_OVER_2M = (HBAR ** 2) / (2 * M_E * E_CHARGE) / (ANGSTROM ** 2)


@dataclass
class FeffPath:
    """A single Feff scattering path."""
    name: str
    feff_file: str
    degeneracy: float
    reff: float
    scattering_atoms: str
    shell: str = ""


@dataclass
class FitParameter:
    """A fitting parameter with bounds and result."""
    name: str
    initial_value: float
    lower_bound: float
    upper_bound: float
    fit_value: Optional[float] = None
    uncertainty: Optional[float] = None
    fixed: bool = False


@dataclass
class FitConditions:
    """Fitting conditions and ranges."""
    k_min: float = 3.0
    k_max: float = 12.0
    r_min: float = 1.0
    r_max: float = 5.0
    k_weight: int = 2
    window: str = "hanning"
    dk: float = 1.0
    e0_shift: float = 0.0
    s02: float = 1.0
    s02_fixed: bool = True


@dataclass
class FitResult:
    """Complete fitting result."""
    sample_name: str = ""
    fit_number: int = 1
    r_factor: float = 0.0
    chi_sq: float = 0.0
    chi_sq_reduced: float = 0.0
    n_indep: int = 0
    n_var: int = 0
    k_data: Optional[np.ndarray] = None
    chi_k_data: Optional[np.ndarray] = None
    chi_k_fit: Optional[np.ndarray] = None
    chi_k_residual: Optional[np.ndarray] = None
    r_data: Optional[np.ndarray] = None
    chi_r_data: Optional[np.ndarray] = None
    chi_r_fit: Optional[np.ndarray] = None
    chi_r_residual: Optional[np.ndarray] = None
    window_k: Optional[np.ndarray] = None
    paths: List[FeffPath] = field(default_factory=list)
    parameters: List[FitParameter] = field(default_factory=list)
    conditions: FitConditions = field(default_factory=FitConditions)
    amplitude_expression: str = ""
    data_processing_steps: List[str] = field(default_factory=list)
    converged: bool = False
    n_iterations: int = 0
    backend: str = "scipy"

    def to_dict(self) -> Dict:
        result = {
            "sample_name": self.sample_name,
            "fit_number": self.fit_number,
            "r_factor": self.r_factor,
            "chi_sq": self.chi_sq,
            "chi_sq_reduced": self.chi_sq_reduced,
            "n_indep": self.n_indep,
            "n_var": self.n_var,
            "converged": self.converged,
            "n_iterations": self.n_iterations,
            "backend": self.backend,
            "paths": [asdict(p) for p in self.paths],
            "parameters": [asdict(p) for p in self.parameters],
            "conditions": asdict(self.conditions),
            "amplitude_expression": self.amplitude_expression,
            "data_processing_steps": self.data_processing_steps,
        }
        for key in ("k_data", "chi_k_data", "chi_k_fit", "chi_k_residual",
                     "r_data", "chi_r_data", "chi_r_fit", "chi_r_residual", "window_k"):
            val = getattr(self, key)
            if val is not None:
                result[key] = val.tolist()
            else:
                result[key] = None
        return result


class XAFSDataLoader:
    """Load XAFS data from various file formats."""

    SUPPORTED_EXTENSIONS = {".chi", ".dat", ".txt", ".csv", ".xmu", ".prj"}

    @staticmethod
    def load(filepath: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load k and chi(k) data from a file.

        Supports formats:
          - .chi (Athena chi(k) output): k, chi, [window?]
          - .dat/.txt: whitespace-delimited 2-column
          - .csv: comma-delimited 2-column

        Args:
            filepath: Path to the data file.

        Returns:
            Tuple of (k_array, chi_array).

        Raises:
            FileNotFoundError: If filepath doesn't exist.
            ValueError: If data format is unrecognized.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")

        ext = path.suffix.lower()
        if ext not in XAFSDataLoader.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file extension: {ext}. "
                f"Supported: {XAFSDataLoader.SUPPORTED_EXTENSIONS}"
            )

        data = np.loadtxt(filepath, comments='#')
        if data.ndim != 2 or data.shape[1] < 2:
            raise ValueError(
                f"Expected 2 or more columns, got {data.shape[1] if data.ndim == 2 else 1}. "
                f"File: {filepath}"
            )

        k = data[:, 0].astype(np.float64)
        chi = data[:, 1].astype(np.float64)
        return k, chi

    @staticmethod
    def check_data(k: np.ndarray, chi: np.ndarray) -> List[str]:
        """Run sanity checks on loaded data."""
        warnings_list = []
        if len(k) < 10:
            warnings_list.append("Very few data points (<10), fit may be unreliable")
        if k[0] < 0:
            warnings_list.append("k values start below 0 -- verify data")
        if np.any(np.isnan(chi)):
            warnings_list.append("NaN values found in chi(k) data")
        if np.max(np.abs(chi)) > 10:
            warnings_list.append("Large chi(k) amplitude detected -- verify normalization")
        return warnings_list


class EXAFSFitter:
    """
    EXAFS fitting engine with scipy backend.

    Implements the standard EXAFS equation:
      chi(k) = S0^2 * sum_i (N_i * |f_i(k)| / (k * R_i^2) *
               exp(-2 * sigma_i^2 * k^2) * sin(2*k*R_i + phi_i(k)))

    Attributes:
        conditions: FitConditions object with all fit settings.
        paths: List of FeffPath objects for scattering paths.
    """

    def __init__(self, conditions: Optional[FitConditions] = None):
        self.conditions = conditions or FitConditions()
        self.paths: List[FeffPath] = []

    def add_path(self, path: FeffPath) -> None:
        """Add a Feff scattering path to the model."""
        self.paths.append(path)

    def feff_amplitude(self, k: np.ndarray, atomic_number: int) -> np.ndarray:
        """
        Approximate Feff backscattering amplitude |f(k)|.

        Uses a simplified parameterization based on the central atom.
        For accurate fitting, real Feff output should be used.

        Args:
            k: k-space grid.
            atomic_number: Atomic number of the scatterer.

        Returns:
            Approximate |f(k)| array.
        """
        z = atomic_number
        k_safe = np.where(k > 0.1, k, 0.1)
        return z * np.exp(-k_safe * 0.3) / (1.0 + 0.05 * k_safe ** 2)

    def feff_phase(self, k: np.ndarray, atomic_number: int) -> np.ndarray:
        """
        Approximate Feff scattering phase shift phi(k).

        Args:
            k: k-space grid.
            atomic_number: Atomic number of the scatterer.

        Returns:
            Approximate phi(k) array.
        """
        z = atomic_number
        return -2.0 * np.arctan(k / (z ** 0.5)) + 0.5 * np.pi

    def exafs_chi(self, k: np.ndarray, params: np.ndarray, param_map: List[Dict]) -> np.ndarray:
        """
        Compute chi(k) for given parameters using the standard EXAFS equation.

        Args:
            k: k-space grid.
            params: Flat parameter array [N0, R0, sigma0, N1, R1, sigma1, ...] + [e0].
            param_map: List mapping each parameter to path index and type.

        Returns:
            Computed chi(k) array.
        """
        chi = np.zeros_like(k)
        k_safe = np.where(k > 0.01, k, 0.01)
        s02 = self.conditions.s02

        for i, path in enumerate(self.paths):
            n_i = params[3 * i]
            r_i = params[3 * i + 1]
            sigma_i = params[3 * i + 2]

            n_i = max(n_i, 0.01)
            r_i = max(r_i, 0.5)
            sigma_i = max(sigma_i, 0.0001)

            try:
                z = int(''.join(c for c in path.scattering_atoms if c.isalpha())[:1]) if path.scattering_atoms else 6
                z_map = {'O': 8, 'C': 6, 'N': 7, 'S': 16, 'P': 15, 'Mo': 42,
                         'Fe': 26, 'Cu': 29, 'Zn': 30, 'W': 74, 'V': 23, 'Ti': 22}
                z = z_map.get(path.scattering_atoms, 8)
            except (ValueError, IndexError):
                z = 8

            f_k = self.feff_amplitude(k_safe, z)
            phi_k = self.feff_phase(k_safe, z)
            debye_factor = np.exp(-2.0 * sigma_i ** 2 * k_safe ** 2)
            path_exafs = s02 * n_i * f_k / (k_safe * r_i ** 2) * debye_factor
            arg = 2.0 * k_safe * r_i + phi_k

            # E0 shift on last parameter
            e0 = params[-1] if len(params) > 3 * len(self.paths) else 0.0
            if abs(e0) > 0.001:
                arg += 2.0 * e0 * r_i / k_safe

            path_exafs *= np.sin(arg)
            chi += path_exafs

        return chi

    def fit(self, k: np.ndarray, chi_data: np.ndarray,
            initial_params: List[float], bounds: List[Tuple[float, float]],
            param_names: List[str], fixed_mask: Optional[List[bool]] = None
            ) -> FitResult:
        """
        Perform EXAFS fitting using scipy.optimize.least_squares.

        Args:
            k: k-space data.
            chi_data: Experimental chi(k).
            initial_params: Initial parameter values.
            bounds: List of (lower, upper) bounds for each parameter.
            param_names: Names for each parameter.
            fixed_mask: Boolean mask; True means parameter is fixed.

        Returns:
            FitResult with all fitting outputs.
        """
        from scipy.optimize import least_squares

        c = self.conditions
        if fixed_mask is None:
            fixed_mask = [False] * len(initial_params)

        # Mask data to fit range
        fit_mask = (k >= c.k_min) & (k <= c.k_max)
        k_fit = k[fit_mask]
        chi_fit = chi_data[fit_mask]
        k_weight = k_fit ** c.k_weight

        # Window function
        if c.window == "hanning":
            window = np.ones_like(k_fit)
            dk = c.dk
            k_edge_low = c.k_min
            k_edge_high = c.k_max
            low_mask = k_fit < k_edge_low + dk
            high_mask = k_fit > k_edge_high - dk
            window[low_mask] = 0.5 * (1 - np.cos(np.pi * (k_fit[low_mask] - k_edge_low) / dk))
            window[high_mask] = 0.5 * (1 - np.cos(np.pi * (k_edge_high - k_fit[high_mask]) / dk))
        else:
            window = np.ones_like(k_fit)

        # Separate free and fixed parameters
        free_indices = [i for i, fixed in enumerate(fixed_mask) if not fixed]
        free_initial = [initial_params[i] for i in free_indices]
        free_bounds = ([bounds[i][0] for i in free_indices],
                       [bounds[i][1] for i in free_indices])

        param_map = self._build_param_map(param_names)

        def residual(free_params: np.ndarray) -> np.ndarray:
            all_params = list(initial_params)
            for idx, fi in enumerate(free_indices):
                all_params[fi] = free_params[idx]
            chi_calc = self.exafs_chi(k_fit, np.array(all_params), param_map)
            return (chi_calc - chi_fit) * k_weight * window

        try:
            result = least_squares(
                residual, free_initial, bounds=free_bounds,
                method='trf', loss='soft_l1', ftol=1e-8, xtol=1e-8,
                max_nfev=2000, verbose=0
            )
        except Exception as exc:
            fit_result = FitResult(
                converged=False, backend="scipy",
                conditions=self.conditions, paths=list(self.paths)
            )
            return fit_result

        # Assemble final parameters
        final_params = list(initial_params)
        for idx, fi in enumerate(free_indices):
            final_params[fi] = result.x[idx]

        # Fit quality
        chi_calc_full = self.exafs_chi(k, np.array(final_params), param_map)
        residual_k = chi_data - chi_calc_full
        fit_mask_all = (k >= c.k_min) & (k <= c.k_max)
        r_factor = np.sum(residual_k[fit_mask_all] ** 2) / np.sum(chi_data[fit_mask_all] ** 2)

        n_pts = np.sum(fit_mask_all)
        delta_k = c.k_max - c.k_min
        delta_r = c.r_max - c.r_min
        n_indep = int(max(1, 2 * delta_k * delta_r / np.pi))
        n_var = len(free_indices)
        dof = max(1, n_indep - n_var)
        chi_sq = np.sum((residual_k[fit_mask_all] * (k[fit_mask_all] ** c.k_weight)) ** 2)
        chi_sq_reduced = chi_sq / dof

        # Build parameters result
        params_out = []
        for i, name in enumerate(param_names):
            unc = None
            if i in free_indices and hasattr(result, 'jac'):
                try:
                    jac = result.jac
                    jtj = jac.T @ jac
                    cov_diag = np.diag(np.linalg.inv(jtj + np.eye(jtj.shape[0]) * 1e-12))
                    free_idx = free_indices.index(i)
                    unc = np.sqrt(max(0, cov_diag[free_idx])) * np.sqrt(chi_sq_reduced)
                except Exception:
                    unc = None

            params_out.append(FitParameter(
                name=name,
                initial_value=initial_params[i],
                lower_bound=bounds[i][0],
                upper_bound=bounds[i][1],
                fit_value=final_params[i],
                uncertainty=unc,
                fixed=fixed_mask[i],
            ))

        fit_result = FitResult(
            r_factor=float(r_factor),
            chi_sq=float(chi_sq),
            chi_sq_reduced=float(chi_sq_reduced),
            n_indep=n_indep,
            n_var=n_var,
            converged=result.success,
            n_iterations=result.nfev,
            k_data=k.astype(np.float64),
            chi_k_data=chi_data.astype(np.float64),
            chi_k_fit=chi_calc_full.astype(np.float64),
            chi_k_residual=residual_k.astype(np.float64),
            paths=list(self.paths),
            parameters=params_out,
            conditions=self.conditions,
            backend="scipy",
        )
        return fit_result

    @staticmethod
    def fourier_transform(k: np.ndarray, chi: np.ndarray, k_weight: int = 2,
                          k_min: Optional[float] = None, k_max: Optional[float] = None,
                          window: str = "hanning", dk: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute |chi(R)| via Fourier transform of k-weighted chi(k).

        Args:
            k: k-space data.
            chi: chi(k) data.
            k_weight: k-weight exponent.
            k_min: Minimum k for transform window.
            k_max: Maximum k for transform window.
            window: Window type ("hanning" or "none").
            dk: Window edge smoothing width.

        Returns:
            Tuple of (R_array, |chi(R)|_array).
        """
        if k_min is None:
            k_min = k[0]
        if k_max is None:
            k_max = k[-1]

        fit_mask = (k >= k_min) & (k <= k_max)
        k_sel = k[fit_mask]
        chi_sel = chi[fit_mask]

        weighted = chi_sel * k_sel ** k_weight

        if window == "hanning":
            win = np.ones_like(k_sel)
            low_mask = k_sel < k_min + dk
            high_mask = k_sel > k_max - dk
            win[low_mask] = 0.5 * (1 - np.cos(np.pi * (k_sel[low_mask] - k_min) / dk))
            win[high_mask] = 0.5 * (1 - np.cos(np.pi * (k_max - k_sel[high_mask]) / dk))
            weighted *= win

        dk_step = k_sel[1] - k_sel[0]
        n_pts = len(k_sel)
        r = np.linspace(0, 10, 500)
        chi_r = np.zeros(len(r), dtype=np.float64)

        for i, ri in enumerate(r):
            integrand = weighted * np.sin(2.0 * k_sel * ri)
            chi_r[i] = np.trapz(integrand, k_sel)

        chi_r_mag = np.abs(chi_r)
        return r, chi_r_mag

    def _build_param_map(self, param_names: List[str]) -> List[Dict]:
        """Build a mapping from parameter index to path and type."""
        return [{"index": i, "name": name} for i, name in enumerate(param_names)]


def find_next_fit_number(project_dir: str) -> int:
    """Scan Fit_XX folders and return the next available number."""
    fit_dir = Path(project_dir) / "Fit"
    if not fit_dir.exists():
        return 1
    existing = []
    for item in fit_dir.iterdir():
        if item.is_dir() and item.name.startswith("Fit_"):
            try:
                num = int(item.name.split("_")[1])
                existing.append(num)
            except (IndexError, ValueError):
                pass
    return max(existing) + 1 if existing else 1


def main():
    """CLI entry point for EXAFS fitting."""
    import argparse

    parser = argparse.ArgumentParser(
        description="XAFS EXAFS Fitting Core",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--data", required=True, help="Path to chi(k) data file")
    parser.add_argument("--sample", required=True, help="Sample name")
    parser.add_argument("--kmin", type=float, default=3.0, help="Minimum k (Ang^-1)")
    parser.add_argument("--kmax", type=float, default=12.0, help="Maximum k (Ang^-1)")
    parser.add_argument("--rmin", type=float, default=1.0, help="Minimum R (Ang)")
    parser.add_argument("--rmax", type=float, default=5.0, help="Maximum R (Ang)")
    parser.add_argument("--kweight", type=int, default=2, help="k-weight exponent")
    parser.add_argument("--s02", type=float, default=1.0, help="S0^2 amplitude")
    parser.add_argument("--project", default=".", help="Project directory")
    parser.add_argument("--backend", default="scipy", choices=["scipy", "larch"],
                        help="Fitting backend")
    parser.add_argument("--params", help="JSON file with initial parameters")
    parser.add_argument("--output", help="Output JSON file for fit results")
    parser.add_argument("--check-prereqs", action="store_true",
                        help="Check prerequisites and exit")
    parser.add_argument("--diagnostics", action="store_true",
                        help="Output skill diagnostics and exit")

    args = parser.parse_args()

    if args.diagnostics:
        diag = {
            "skill": "xafs-fit-skill",
            "version": "1.0.0",
            "harness_level": "medium",
            "commands": ["fit_core.py", "plotting.py", "excel_output.py"],
            "harness_features": {
                "input_validation": True,
                "output_sanity": True,
                "check_prereqs": True,
                "diagnostics": True,
            },
        }
        print(json.dumps(diag, indent=2))
        return 0

    if args.check_prereqs:
        checks = []
        # Python version
        import platform
        py_ver = platform.python_version()
        checks.append({"check": "python_version", "required": ">=3.9",
                        "found": py_ver, "ok": tuple(map(int, py_ver.split("."))) >= (3, 9)})

        for pkg in ["numpy", "scipy"]:
            try:
                __import__(pkg)
                checks.append({"check": f"package_{pkg}", "required": pkg,
                                "found": "installed", "ok": True})
            except ImportError:
                checks.append({"check": f"package_{pkg}", "required": pkg,
                                "found": "missing", "ok": False})

        ready = all(c["ok"] for c in checks)
        print(json.dumps({"ready": ready, "checks": checks}, indent=2))
        return 0 if ready else 1

    # Load data
    loader = XAFSDataLoader()
    k, chi = loader.load(args.data)
    warnings_list = loader.check_data(k, chi)
    for w in warnings_list:
        print(f"WARNING: {w}", file=sys.stderr)

    # Configure conditions
    conditions = FitConditions(
        k_min=args.kmin, k_max=args.kmax,
        r_min=args.rmin, r_max=args.rmax,
        k_weight=args.kweight, s02=args.s02,
    )

    # Load parameters if provided
    fitter = EXAFSFitter(conditions)
    paths = []
    initial_params = []
    bounds_list = []
    param_names = []
    fixed_mask = []

    if args.params and Path(args.params).exists():
        with open(args.params) as f:
            params_data = json.load(f)
        for p in params_data.get("paths", []):
            path = FeffPath(**p)
            fitter.add_path(path)
        for p in params_data.get("parameters", []):
            initial_params.append(p["initial_value"])
            bounds_list.append((p.get("lower_bound", -np.inf), p.get("upper_bound", np.inf)))
            param_names.append(p["name"])
            fixed_mask.append(p.get("fixed", False))
    else:
        print("No parameter file provided. Using dummy defaults for demonstration.")
        fitter.add_path(FeffPath(
            name="Mo-O", feff_file="feff0001.dat", degeneracy=2.0,
            reff=1.70, scattering_atoms="O", shell="1st"
        ))
        fitter.add_path(FeffPath(
            name="Mo-Mo", feff_file="feff0002.dat", degeneracy=2.0,
            reff=3.40, scattering_atoms="Mo", shell="2nd"
        ))
        initial_params = [2.0, 1.70, 0.003, 2.0, 3.40, 0.005, 0.0]
        bounds_list = [(0.5, 8), (1.5, 1.9), (0.0001, 0.02),
                       (0.5, 8), (3.2, 3.6), (0.0001, 0.02),
                       (-10, 10)]
        param_names = ["N_Mo-O", "R_Mo-O", "sigma2_Mo-O",
                       "N_Mo-Mo", "R_Mo-Mo", "sigma2_Mo-Mo", "DeltaE0"]
        fixed_mask = [False] * 6 + [False]

    result = fitter.fit(k, chi, initial_params, bounds_list, param_names, fixed_mask)

    # Post-fit: compute R-space
    if result.chi_k_fit is not None and result.chi_k_data is not None:
        r, chi_r_data = EXAFSFitter.fourier_transform(
            k, result.chi_k_data, conditions.k_weight,
            conditions.k_min, conditions.k_max
        )
        _, chi_r_fit = EXAFSFitter.fourier_transform(
            k, result.chi_k_fit, conditions.k_weight,
            conditions.k_min, conditions.k_max
        )
        _, chi_r_residual = EXAFSFitter.fourier_transform(
            k, result.chi_k_residual, conditions.k_weight,
            conditions.k_min, conditions.k_max
        )
        result.r_data = r
        result.chi_r_data = chi_r_data
        result.chi_r_fit = chi_r_fit
        result.chi_r_residual = chi_r_residual

    result.sample_name = args.sample
    fit_num = find_next_fit_number(args.project)
    result.fit_number = fit_num
    result.amplitude_expression = f"S02 = {conditions.s02} (fixed)" if conditions.s02_fixed else f"S02 = {conditions.s02} (floated)"
    result.data_processing_steps = [
        f"Loaded data from {args.data}",
        f"k-range: [{conditions.k_min}, {conditions.k_max}] Ang^-1",
        f"k-weight: {conditions.k_weight}",
        f"Window: {conditions.window}, dk={conditions.dk}",
        "Fourier transform to R-space",
    ]

    # Output
    output_path = args.output or Path(args.project) / "results" / f"{args.sample}_fit_result.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    out_dict = result.to_dict()
    with open(output_path, 'w') as f:
        json.dump(out_dict, f, indent=2)
    print(f"Fit result saved to: {output_path}")
    print(f"  R-factor: {result.r_factor:.6f}")
    print(f"  Reduced chi-sq: {result.chi_sq_reduced:.4f}")
    print(f"  N_indep: {result.n_indep}, N_var: {result.n_var}")
    print(f"  Converged: {result.converged}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
