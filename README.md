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

## How to Use

1. **Install dependencies:** Make sure PyMOL is installed (with a Python environment supporting `from pymol import cmd`) and install `python-docx`:
   ```bash
   pip install -r requirements.txt
   ```
2. Put the code file (`pymol_structure_analysis.py`) and your two `.pdb` files into the same folder.
3. Open the code file and change the residue number (`resi_num`), chain ID (`chain_id` if needed), and the PDB file names to match the files you put in the folder, then save the code file.
4. Open PyMOL and go into that folder using the `cd` command:
   ```text
   cd /path/to/your/folder
   ```
5. Run the script inside PyMOL:
   ```text
   run pymol_structure_analysis.py
   ```

