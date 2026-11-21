# PyMOL SNP Protein Structure Comparison

Automated PyMOL script (`pymol_structure_analysis.py`) for comparing wild-type and SNP variant protein structures around a target residue, rendering a structural overlay figure (`.png`), and generating a formatted Word matrix report (`.docx`).

## Features
- Aligns wild-type and variant PDB structures in PyMOL
- Computes local backbone Cα RMSD across a ±4 residue window around the target site
- Extracts backbone dihedral angles (Φ, Ψ) with circular wrap-around (ΔΦ, ΔΨ)
- Assigns and compares secondary structure via DSSP
- Exports a high-resolution comparison figure (`.png`) and a formatted Word matrix report (`.docx`)

## Requirements
- **PyMOL** (installed with a Python environment that supports `from pymol import cmd`)
- **`python-docx`**:
  ```bash
  pip install -r requirements.txt
  ```

## What to Change to Reuse with Your Own Data

1. **Change the residue number and chain ID** (lines **67–68** in `pymol_structure_analysis.py`): Open `pymol_structure_analysis.py`, update `70` and `"A"` to match your target residue number and chain, and save the file:
   ```python
   # Line 67
   resi_num = int(cli_args[2]) if len(cli_args) >= 3 else 70
   # Line 68
   chain_id = cli_args[3] if len(cli_args) >= 4 else "A"
   ```

2. **Place your PDB files in the same folder:** Put `pymol_structure_analysis.py` and your two `.pdb` files in the same folder (no code edits needed for the PDB file names; including `wt` or `wild` in the wild-type file name helps the script recognize it automatically).

## How to Use

1. **Install dependencies:** Make sure PyMOL is installed (with a Python environment supporting `from pymol import cmd`) and install `python-docx`:
   ```bash
   pip install -r requirements.txt
   ```
2. **Navigate to your folder inside PyMOL:**
   ```text
   cd /path/to/your/folder
   ```
3. **Run the script inside PyMOL:**
   ```text
   run pymol_structure_analysis.py
   ```
