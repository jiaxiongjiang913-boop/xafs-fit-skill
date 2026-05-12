#!/usr/bin/env python3
"""
Input validation utilities for XAFS fitting parameters.

Validates all user-facing inputs before computation:
rejects invalid values, reports structured JSON errors to stderr.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional


def validate_fit_params(
    k_min: float, k_max: float,
    r_min: float, r_max: float,
    k_weight: int,
    s02: float,
    params_list: Optional[List[Dict]] = None,
) -> Tuple[bool, List[Dict]]:
    """
    Validate XAFS fitting parameters.

    Args:
        k_min, k_max: k-range bounds (Ang^-1).
        r_min, r_max: R-range bounds (Ang).
        k_weight: k-weight exponent.
        s02: S0^2 amplitude.
        params_list: Optional list of parameter dicts.

    Returns:
        Tuple of (is_valid, errors_list).
        Each error: {"field": str, "error": str, "error_type": "validation"}
    """
    errors = []

    # k-range
    if k_min < 0:
        errors.append({"field": "k_min", "error": f"k_min must be >= 0, got {k_min}"})
    if k_max <= 0:
        errors.append({"field": "k_max", "error": f"k_max must be > 0, got {k_max}"})
    if k_min >= k_max:
        errors.append({"field": "k_range", "error": f"k_min ({k_min}) >= k_max ({k_max})"})
    if k_max > 25:
        errors.append({"field": "k_max", "error": f"k_max ({k_max}) unusually large (>25)"})

    # R-range
    if r_min < 0:
        errors.append({"field": "r_min", "error": f"r_min must be >= 0, got {r_min}"})
    if r_max <= 0:
        errors.append({"field": "r_max", "error": f"r_max must be > 0, got {r_max}"})
    if r_min >= r_max:
        errors.append({"field": "r_range", "error": f"r_min ({r_min}) >= r_max ({r_max})"})
    if r_max > 10:
        errors.append({"field": "r_max", "error": f"r_max ({r_max}) unusually large (>10)"})

    # k-weight
    if k_weight not in (1, 2, 3):
        errors.append({"field": "k_weight", "error": f"k_weight must be 1, 2, or 3, got {k_weight}"})

    # S02
    if s02 <= 0 or s02 > 1.5:
        errors.append({"field": "s02", "error": f"S0^2 must be in (0, 1.5], got {s02}"})

    # Per-parameter checks
    if params_list:
        for i, p in enumerate(params_list):
            name = p.get("name", f"param_{i}")
            if p.get("lower_bound", -1) >= p.get("upper_bound", 1):
                errors.append({
                    "field": f"param_{name}_bounds",
                    "error": f"lower >= upper for {name}"
                })
            init = p.get("initial_value")
            lb = p.get("lower_bound", float("-inf"))
            ub = p.get("upper_bound", float("inf"))
            if init is not None and (init < lb or init > ub):
                errors.append({
                    "field": f"param_{name}_init",
                    "error": f"initial ({init}) outside bounds [{lb}, {ub}]"
                })

    return len(errors) == 0, errors


def validate_data_file(filepath: str) -> Tuple[bool, List[Dict]]:
    """
    Validate that a data file exists and is readable.

    Args:
        filepath: Path to data file.

    Returns:
        Tuple of (is_valid, errors_list).
    """
    errors = []
    if not filepath:
        errors.append({"field": "data_file", "error": "No file path provided"})
        return False, errors

    path = Path(filepath)
    if not path.exists():
        errors.append({"field": "data_file", "error": f"File not found: {filepath}"})
    elif not path.is_file():
        errors.append({"field": "data_file", "error": f"Not a file: {filepath}"})
    elif path.stat().st_size == 0:
        errors.append({"field": "data_file", "error": f"File is empty: {filepath}"})

    return len(errors) == 0, errors


def validate_project_dir(dirpath: str) -> Tuple[bool, List[Dict]]:
    """
    Validate that a project directory exists or can be created.

    Args:
        dirpath: Project directory path.

    Returns:
        Tuple of (is_valid, errors_list).
    """
    errors = []
    if not dirpath:
        errors.append({"field": "project_dir", "error": "No project directory provided"})
        return False, errors

    path = Path(dirpath)
    if path.exists() and not path.is_dir():
        errors.append({"field": "project_dir", "error": f"Path exists but is not a directory: {dirpath}"})

    return len(errors) == 0, errors


def validate_fe各路_paths(paths: List[Dict]) -> Tuple[bool, List[Dict]]:
    """Validate Feff path definitions."""
    errors = []
    required_keys = {"name", "degeneracy", "reff", "scattering_atoms"}
    for i, path in enumerate(paths):
        missing = required_keys - set(path.keys())
        if missing:
            errors.append({
                "field": f"feff_path_{i}",
                "error": f"Missing required keys: {missing}"
            })
        if path.get("degeneracy", 0) <= 0:
            errors.append({
                "field": f"feff_path_{i}_degen",
                "error": f"Degeneracy must be > 0, got {path.get('degeneracy')}"
            })
        if path.get("reff", 0) <= 0:
            errors.append({
                "field": f"feff_path_{i}_reff",
                "error": f"Reff must be > 0, got {path.get('reff')}"
            })
    return len(errors) == 0, errors


def output_sanity_check(result: Dict) -> List[Dict]:
    """
    Post-fit sanity checks on the result.

    Args:
        result: Fit result dict.

    Returns:
        List of warning dicts.
    """
    warnings = []

    r_factor = result.get("r_factor", 0)
    if r_factor > 0.1:
        warnings.append({"field": "r_factor", "warning": f"R-factor is large ({r_factor:.4f}), fit may be poor"})
    if r_factor < 1e-6:
        warnings.append({"field": "r_factor", "warning": "R-factor is suspiciously small -- verify"})

    chi_sq_red = result.get("chi_sq_reduced", 0)
    if chi_sq_red > 100:
        warnings.append({"field": "chi_sq_reduced", "warning": f"Reduced chi-sq is very large ({chi_sq_red:.1f})"})

    params = result.get("parameters", [])
    for p in params:
        name = p.get("name", "")
        fit_val = p.get("fit_value")
        lb = p.get("lower_bound", float("-inf"))
        ub = p.get("upper_bound", float("inf"))
        if fit_val is not None and (fit_val <= lb or fit_val >= ub):
            warnings.append({
                "field": f"param_{name}",
                "warning": f"Fit value ({fit_val}) at bound [{lb}, {ub}]"
            })

    return warnings


def main():
    """CLI: validate inputs and print structured JSON result."""
    import argparse

    parser = argparse.ArgumentParser(description="XAFS Input Validator")
    parser.add_argument("--file", help="Data file to validate")
    parser.add_argument("--project", help="Project directory to validate")
    parser.add_argument("--params-json", help="JSON file with fit parameters to validate")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check-prereqs")
    sub.add_parser("diagnostics")

    args = parser.parse_args()

    if args.command == "diagnostics":
        diag = {
            "skill": "xafs-fit-skill",
            "component": "validators",
            "version": "1.0.0",
        }
        print(json.dumps(diag, indent=2))
        return 0

    if args.command == "check-prereqs":
        checks = [
            {"check": "python_version", "required": ">=3.9",
             "found": sys.version.split()[0], "ok": sys.version_info >= (3, 9)},
        ]
        ready = all(c["ok"] for c in checks)
        print(json.dumps({"ready": ready, "checks": checks}, indent=2))
        return 0 if ready else 1

    all_errors = []

    if args.file:
        _, errs = validate_data_file(args.file)
        all_errors.extend(errs)

    if args.project:
        _, errs = validate_project_dir(args.project)
        all_errors.extend(errs)

    if args.params_json:
        with open(args.params_json) as f:
            pdata = json.load(f)
        _, errs = validate_fit_params(
            k_min=pdata.get("k_min", 0),
            k_max=pdata.get("k_max", 0),
            r_min=pdata.get("r_min", 0),
            r_max=pdata.get("r_max", 0),
            k_weight=pdata.get("k_weight", 2),
            s02=pdata.get("s02", 1.0),
            params_list=pdata.get("parameters"),
        )
        all_errors.extend(errs)

    if all_errors:
        result = {"error": "Validation failed", "error_type": "validation", "details": all_errors}
        print(json.dumps(result, indent=2), file=sys.stderr)
        return 1

    print(json.dumps({"valid": True, "errors": []}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
