Automated PyMOL script (`pymol_structure_analysis.py`) for comparing wild-type and SNP variant protein structures around a target residue, rendering a structural overlay figure (`.png`), and generating a formatted Word matrix report (`.docx`)[cite: 13].

## Features
- Aligns wild-type and variant PDB structures in PyMOL[cite: 13]
- Computes local backbone Cα RMSD across a ±4 residue window around the target site[cite: 13]
- Extracts backbone dihedral angles (Φ, Ψ) with circular wrap-around (ΔΦ, ΔΨ)[cite: 13]
- Assigns and compares secondary structure via DSSP[cite: 13]
- Exports a high-resolution comparison figure (`.png`) and a formatted Word matrix report (`.docx`)[cite: 13]

## Requirements
- **PyMOL** (installed with a Python environment that supports `from pymol import cmd`)[cite: 13]
- **`python-docx`**:[cite: 13]
  ```bash
  pip install -r requirements.txt
  ```

## Where to Make Changes Before Running

1. **Put the files together:** Place `pymol_structure_analysis.py` and your two `.pdb` files (wild-type and variant) in the same folder[cite: 13].
2. **Change the default residue number and chain ID inside `pymol_structure_analysis.py`:** Open `pymol_structure_analysis.py` and update `70` and `"A"` to match your target residue and chain:
 ```python
   # Line 45
   resi_num = int(cli_args[2]) if len(cli_args) >= 3 else 70
   # Line 46
   chain_id = cli_args[3] if len(cli_args) >= 4 else "A"
   ```
   ```
3.**Change the PDB file names** (around lines 42–43 in `pymol_structure_analysis.py`): Put `pymol_structure_analysis.py` and your two `.pdb` files in the same folder, then update these lines:
   ```python
   # Line 42
   wt_file = "wildtype.pdb"
   # Line 43
   mut_file = "mutant.pdb"
   ```
## How to Use

1. **Install dependencies:** Make sure PyMOL is installed (with a Python environment supporting `from pymol import cmd`) and install `python-docx`[cite: 13]:
   ```bash
   pip install -r requirements.txt
   ```
2. **Open PyMOL and go into your folder using `cd`:**[cite: 13]
   ```text
   cd /path/to/your/folder
   ```
3. **Run the script inside PyMOL:**[cite: 13]
   ```text
   run pymol_structure_analysis.py
   ```
   *(Or pass your PDB filenames, residue number, and chain ID directly: `run pymol_structure_analysis.py wt.pdb mut.pdb 70 A`.)*
