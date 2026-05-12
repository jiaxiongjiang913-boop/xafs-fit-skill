#!/usr/bin/env python3
"""
XAFS Publication Figure Generator.

Generates PDF (2-page) and PNG (figure-only) outputs for XAFS fitting results.
- PDF Page 1: Overview -- k-space fit (data + fit + window)
- PDF Page 2: Details -- R-space fit (data + fit + residual) + parameter table
- PNG: R-space fit (data + fit only, no residual, no table)

All figures use LaTeX math mode for proper superscript/subscript formatting
(e.g., $S_0^2$, $\sigma^2$, $\chi^2_\nu$, $\AA^{-1}$).

Example:
    $ python plotting.py --result fit_result.json --output ./Fit/Fit_01/
"""

import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "mathtext.default": "regular",
    "axes.linewidth": 1.2,
    "xtick.major.width": 1.2,
    "ytick.major.width": 1.2,
    "xtick.major.size": 5,
    "ytick.major.size": 5,
    "legend.fontsize": 9,
    "figure.dpi": 150,
})


class XAFSFigureGenerator:
    """Generate publication-quality XAFS fitting figures."""

    def __init__(self, result: Dict):
        """
        Initialize with a fit result dict.

        Args:
            result: Fit result dict (from fit_core.py output JSON or FitResult.to_dict()).
        """
        self.result = result
        self.sample = result.get("sample_name", "Sample")
        self.conditions = result.get("conditions", {})
        self._validate()

    def _validate(self) -> None:
        """Validate that required data arrays are present."""
        required = ["k_data", "chi_k_data", "chi_k_fit", "r_data", "chi_r_data", "chi_r_fit"]
        missing = [k for k in required if k not in self.result or self.result[k] is None]
        if missing:
            raise ValueError(
                f"Missing required data arrays: {missing}. "
                f"Ensure fit_core.py ran successfully before plotting."
            )

    def _make_k_space_figure(self, ax: plt.Axes) -> None:
        """Draw k-space fit overview on a given axes."""
        k = np.array(self.result["k_data"])
        chi_data = np.array(self.result["chi_k_data"])
        chi_fit = np.array(self.result["chi_k_fit"])
        residual = np.array(self.result.get("chi_k_residual", []))
        window_k = np.array(self.result.get("window_k", []))

        kw = self.conditions.get("k_weight", 2)
        kmin = self.conditions.get("k_min", k[0])
        kmax = self.conditions.get("k_max", k[-1])

        kw_data = chi_data * k ** kw
        kw_fit = chi_fit * k ** kw
        kw_res = residual * k ** kw if len(residual) > 0 else None

        ax.plot(k, kw_data, 'k-', linewidth=0.8, label='Data')
        ax.plot(k, kw_fit, 'r-', linewidth=1.0, label='Fit')

        if kw_res is not None and len(kw_res) == len(k):
            ax.plot(k, kw_res - np.ptp(kw_data) * 0.3, 'b-', linewidth=0.6, label='Residual')

        ax.axhline(y=0, color='gray', linewidth=0.4, linestyle='--')
        ax.axvline(x=kmin, color='green', linewidth=0.6, linestyle=':', alpha=0.7)
        ax.axvline(x=kmax, color='green', linewidth=0.6, linestyle=':', alpha=0.7)

        rfac = self.result.get("r_factor", 0)
        ax.text(0.03, 0.95,
                f"{self.sample}\n$R$-factor = {rfac:.4f}\nk-weight = {kw}",
                transform=ax.transAxes, fontsize=8, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

        ax.set_xlabel(r'$k\ (\AA^{-1})$')
        ax.set_ylabel(r'$k^{%d}\chi(k)\ (\AA^{-%d})$' % (kw, kw))
        ax.legend(loc='upper right')

    def _make_r_space_figure(self, ax: plt.Axes, include_residual: bool = True) -> None:
        """Draw R-space fit on a given axes."""
        r = np.array(self.result["r_data"])
        chi_r_data = np.array(self.result["chi_r_data"])
        chi_r_fit = np.array(self.result["chi_r_fit"])
        chi_r_residual = np.array(self.result.get("chi_r_residual", []))

        ax.plot(r, chi_r_data, 'k-', linewidth=0.8, label='Data')
        ax.plot(r, chi_r_fit, 'r-', linewidth=1.0, label='Fit')

        if include_residual and len(chi_r_residual) == len(r):
            shift = np.ptp(chi_r_data) * 0.4
            ax.plot(r, chi_r_residual - shift, 'b-', linewidth=0.6, label='Residual')
            ax.axhline(y=-shift, color='gray', linewidth=0.4, linestyle='--')

        ax.set_xlabel(r'$R\ (\AA)$')
        ax.set_ylabel(r'$|\chi(R)|\ (\AA^{-3})$')
        ax.legend(loc='upper right')

    def _make_parameter_table(self, ax: plt.Axes) -> None:
        """Draw parameter table on a given axes."""
        ax.axis("off")

        params = self.result.get("parameters", [])
        conditions = self.result.get("conditions", {})
        paths = self.result.get("paths", [])

        lines = []
        lines.append("=" * 70)

        # Fit Quality
        lines.append("Fit Quality")
        lines.append("-" * 40)
        lines.append(f"  R-factor:        {self.result.get('r_factor', 0):.6f}")
        lines.append(f"  Reduced $\\chi^2_\\nu$:  {self.result.get('chi_sq_reduced', 0):.4f}")
        lines.append(f"  $N_{{\\rm indep}}$:       {self.result.get('n_indep', 0)}")
        lines.append(f"  $N_{{\\rm var}}$:         {self.result.get('n_var', 0)}")
        lines.append("")

        # Structure Parameters
        lines.append("Structure Parameters")
        lines.append("-" * 70)
        header = f"  {'Path':<12s}  {'N':>6s}  {'R (\\AA)':>8s}  {'$\\sigma^2$ (\\AA$^2$)':>16s}  {'$\\Delta E_0$ (eV)':>14s}"
        lines.append(header)
        lines.append("  " + "-" * 66)

        n_paths = len(paths)
        for i, p in enumerate(params):
            if i >= n_paths:
                path_name = "E0"
            else:
                path_name = paths[i].get("name", f"Path{i+1}")

            if p.get("name", "").startswith("DeltaE"):
                continue

            n_val = p.get("fit_value", p.get("initial_value", 0))
            unc = p.get("uncertainty")

            if "R_" in p.get("name", ""):
                if unc:
                    lines.append(f"  {path_name:<12s}  {n_val:6.3f}  {unc:8.4f}")
                else:
                    lines.append(f"  {path_name:<12s}  {n_val:6.3f}")
            elif "sigma" in p.get("name", "").lower():
                val_str = f"{n_val:.5f}"
                if unc:
                    val_str += f" +/- {unc:.5f}"
                lines.append(f"  {path_name:<12s}  {'':>6s}  {'':>8s}  {val_str:>16s}")
            elif "N_" in p.get("name", ""):
                val_str = f"{n_val:.1f}"
                if unc:
                    val_str += f" +/- {unc:.2f}"
                lines.append(f"  {path_name:<12s}  {val_str:>6s}")
            else:
                lines.append(f"  {path_name:<12s}  {n_val:6.3f}")

        n_paths_fitted = sum(1 for p in params if not p.get("fixed", False))
        for p in params:
            if p.get("name", "").startswith("DeltaE"):
                val_str = f"{p.get('fit_value', 0):.2f}"
                unc = p.get("uncertainty")
                if unc:
                    val_str += f" +/- {unc:.2f}"
                lines.append(f"  {'DeltaE0':<12s}  {val_str:>6s}")

        lines.append("")

        # Conditions
        lines.append("Fit Conditions")
        lines.append("-" * 40)
        lines.append(f"  $k$-range:         {conditions.get('k_min', 'N/A')} - {conditions.get('k_max', 'N/A')} $\\AA^{{-1}}$")
        lines.append(f"  $R$-range:         {conditions.get('r_min', 'N/A')} - {conditions.get('r_max', 'N/A')} $\\AA$")
        lines.append(f"  $k$-weight:        {conditions.get('k_weight', 'N/A')}")
        lines.append(f"  Window:            {conditions.get('window', 'N/A')}")
        lines.append(f"  $S_0^2$:           {conditions.get('s02', 'N/A')} ({'fixed' if conditions.get('s02_fixed', True) else 'floated'})")
        lines.append("=" * 70)

        text = "\n".join(lines)
        ax.text(0.05, 0.98, text, transform=ax.transAxes, fontsize=7.5,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.9))

    def generate_pdf(self, output_path: str) -> str:
        """
        Generate 2-page PDF:
          Page 1: k-space overview (data + fit + window)
          Page 2: R-space fit + parameter table

        Args:
            output_path: Output PDF file path.

        Returns:
            The output path.
        """
        with PdfPages(output_path) as pdf:
            # Page 1: k-space overview
            fig1, ax1 = plt.subplots(figsize=(8, 5))
            self._make_k_space_figure(ax1)
            fig1.tight_layout(pad=1.5)
            pdf.savefig(fig1, dpi=150)
            plt.close(fig1)

            # Page 2: R-space fit with parameter table
            fig2 = plt.figure(figsize=(8, 10))
            gs = fig2.add_gridspec(2, 1, height_ratios=[1, 1.2], hspace=0.35)

            ax2_r = fig2.add_subplot(gs[0])
            self._make_r_space_figure(ax2_r, include_residual=True)

            ax2_table = fig2.add_subplot(gs[1])
            self._make_parameter_table(ax2_table)

            fig2.suptitle(f"EXAFS Fit: {self.sample}", fontweight='bold', fontsize=13, y=0.98)
            fig2.tight_layout(pad=1.5, rect=[0, 0, 1, 0.96])
            pdf.savefig(fig2, dpi=150)
            plt.close(fig2)

        return output_path

    def generate_png(self, output_path: str) -> str:
        """
        Generate PNG figure: R-space data + fit only (no residual, no table).

        Args:
            output_path: Output PNG file path.

        Returns:
            The output path.
        """
        fig, ax = plt.subplots(figsize=(8, 5))
        self._make_r_space_figure(ax, include_residual=False)
        ax.set_title(f"EXAFS Fit: {self.sample}", fontweight='bold')
        fig.tight_layout(pad=1.5)
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        return output_path

    def generate_all(self, output_dir: str) -> Tuple[str, str]:
        """
        Generate both PDF and PNG outputs.

        Args:
            output_dir: Directory to save outputs.

        Returns:
            Tuple of (pdf_path, png_path).
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        sample = self.sample.replace(" ", "_")
        pdf_path = str(out_dir / f"{sample}_fit.pdf")
        png_path = str(out_dir / f"{sample}_fit.png")

        self.generate_pdf(pdf_path)
        self.generate_png(png_path)

        print(f"Generated: {pdf_path}")
        print(f"Generated: {png_path}")
        return pdf_path, png_path


def main():
    """CLI entry point for figure generation."""
    import argparse

    parser = argparse.ArgumentParser(description="XAFS Publication Figure Generator")
    parser.add_argument("--result", required=True, help="Path to fit result JSON")
    parser.add_argument("--output", required=True, help="Output directory (e.g., Fit/Fit_01/)")
    parser.add_argument("--png-only", action="store_true", help="Generate only PNG")
    parser.add_argument("--pdf-only", action="store_true", help="Generate only PDF")
    parser.add_argument("--check-prereqs", action="store_true",
                        help="Check prerequisites and exit")
    parser.add_argument("--diagnostics", action="store_true",
                        help="Output skill diagnostics and exit")

    args = parser.parse_args()

    if args.diagnostics:
        import json as jmod
        diag = {
            "skill": "xafs-fit-skill",
            "component": "plotting",
            "version": "1.0.0",
            "harness_features": {"input_validation": True, "output_sanity": True},
        }
        print(jmod.dumps(diag, indent=2))
        return 0

    if args.check_prereqs:
        checks = []
        for pkg in ["numpy", "matplotlib"]:
            try:
                __import__(pkg)
                checks.append({"check": f"package_{pkg}", "required": pkg,
                                "found": "installed", "ok": True})
            except ImportError:
                checks.append({"check": f"package_{pkg}", "required": pkg,
                                "found": "missing", "ok": False})

        import platform
        py_ver = platform.python_version()
        checks.append({"check": "python_version", "required": ">=3.9",
                        "found": py_ver, "ok": tuple(map(int, py_ver.split("."))) >= (3, 9)})

        ready = all(c["ok"] for c in checks)
        print(json.dumps({"ready": ready, "checks": checks}, indent=2))
        return 0 if ready else 1

    with open(args.result) as f:
        result = json.load(f)

    gen = XAFSFigureGenerator(result)

    if args.png_only:
        gen.generate_png(str(Path(args.output) / f"{gen.sample}_fit.png"))
    elif args.pdf_only:
        gen.generate_pdf(str(Path(args.output) / f"{gen.sample}_fit.pdf"))
    else:
        gen.generate_all(args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
