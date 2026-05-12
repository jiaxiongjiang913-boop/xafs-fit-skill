# xafs-fit-skill -- XAFS Interactive Fitting

Interactive XAFS (X-ray Absorption Fine Structure) fitting skill supporting EXAFS and XANES analysis with multiple backends (Larch, scipy, Demeter/Artemis).

## Installation

### Using install.sh (Recommended)

```bash
chmod +x install.sh
./install.sh                          # Auto-detect platform
./install.sh --platform claude-code   # Claude Code
./install.sh --platform cursor        # Cursor (auto-generates .mdc)
./install.sh --all                    # All detected platforms
./install.sh --dry-run                # Preview without installing
```

### Universal Path (works with 6+ tools)

```bash
git clone <repo-url> ~/.agents/skills/xafs-fit-skill
```

Works with Codex CLI, Gemini CLI, Kiro, Antigravity, and other tools that read `~/.agents/skills/`.

### Manual Installation

| Platform | Copy to |
|----------|---------|
| Universal | `~/.agents/skills/xafs-fit-skill/` |
| Claude Code | `~/.claude/skills/xafs-fit-skill/` or `.claude/skills/xafs-fit-skill/` |
| GitHub Copilot | `.github/skills/xafs-fit-skill/` |
| Cursor | `.cursor/rules/xafs-fit-skill/` |
| Windsurf | `.windsurf/rules/xafs-fit-skill/` |
| Cline | `.clinerules/xafs-fit-skill/` |
| Codex CLI | `~/.agents/skills/xafs-fit-skill/` |
| Gemini CLI | `~/.gemini/skills/xafs-fit-skill/` |
| Kiro | `.kiro/skills/xafs-fit-skill/` |
| Trae | `.trae/rules/xafs-fit-skill/` |
| Goose | `~/.config/goose/skills/xafs-fit-skill/` |
| OpenCode | `~/.config/opencode/skills/xafs-fit-skill/` |
| Roo Code | `.roo/rules/xafs-fit-skill/` |
| Antigravity | `.agents/skills/xafs-fit-skill/` |

## Prerequisites

1. **Python >= 3.9**
2. **Required packages**:
   ```bash
   pip install numpy scipy matplotlib openpyxl
   ```
3. **Optional**: Larch backend: `pip install xraylarch`
4. No API keys required (local computation only)

## Usage Examples

### Interactive Fitting

```
/xafs-fit
> 我来帮你做 XAFS 拟合。请回答几个问题...
> 1. 使用什么软件？[Larch / scipy / Demeter]
> 2. 数据文件在哪里？
> 3. 样品名称是什么？
```

### CLI Usage

```bash
# Fit with scipy backend
python scripts/fit_core.py --data sample.chi --sample a-MoO3 \
    --kmin 3 --kmax 12 --rmin 1 --rmax 5 --kweight 2 \
    --project ./my_project

# Generate figures from fit result
python scripts/plotting.py --result fit_result.json --output ./Fit/Fit_01/

# Generate Excel parameter file
python scripts/excel_output.py --result fit_result.json --output ./Fit/Fit_01/sample_parameters.xlsx

# Check prerequisites
python scripts/fit_core.py --check-prereqs

# Show diagnostics
python scripts/fit_core.py --diagnostics
```

### Output Structure

```
project_dir/
├── Fit/
│   ├── Fit_01/
│   │   ├── sample_fit.pdf          # 2 pages: overview + details+table
│   │   ├── sample_fit.png          # Figure only
│   │   └── sample_fit_parameters.xlsx
│   ├── Fit_02/                     # Re-fits auto-increment
│   └── ...
└── results/
    └── sample_fit_report.txt
```

## How It Works

1. **Gather info**: The skill asks about your data, sample, and fitting requirements
2. **Configure**: Set k-range, R-range, k-weight, paths, and parameters
3. **Fit**: EXAFS fitting via scipy least_squares with the standard EXAFS equation
4. **Output**: Auto-generates publication-ready PDF (LaTeX math), PNG, and Excel files
5. **Iterate**: Adjust parameters and re-fit -- old results are never overwritten

## Troubleshooting

See `references/troubleshooting.md` for common issues:
- Fit does not converge
- Unphysical parameter values
- Missing dependencies
- LaTeX rendering issues

## Version History

- v1.0.0 (2026-05-13): Initial release with scipy backend, PDF/PNG/Excel output.
