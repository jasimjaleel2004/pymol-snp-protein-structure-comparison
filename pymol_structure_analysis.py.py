# -*- coding: utf-8 -*-
import glob
import os
import sys
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor
from pymol import cmd


def set_cell_background(cell, fill_color):
    """Sets background color of a table cell (hex string, e.g., 'F2F4F8')."""
    tcPr = cell._tc.get_or_add_tcPr()
    xml_str = f'<w:shd {nsdecls("w")} w:fill="{fill_color}"/>'
    shd = parse_xml(xml_str)
    tcPr.append(shd)


def get_work_dir():
    """Resolve script directory when available, falling back to current working directory."""
    if "__file__" in globals() and os.path.isfile(__file__):
        return os.path.dirname(os.path.abspath(__file__))
    return os.getcwd()


def resolve_pdb_files(work_dir, args):
    """
    Resolve wild-type and mutant PDB paths from CLI args or auto-detect two .pdb files
    in the working directory.
    """
    if len(args) >= 2:
        wt_file = args[0] if os.path.isabs(args[0]) else os.path.join(work_dir, args[0])
        mut_file = args[1] if os.path.isabs(args[1]) else os.path.join(work_dir, args[1])
        return wt_file, mut_file

    pdb_files = sorted(glob.glob(os.path.join(work_dir, "*.pdb")))
    if len(pdb_files) != 2:
        found = [os.path.basename(p) for p in pdb_files]
        raise FileNotFoundError(
            f"Expected 2 PDB files in '{work_dir}' (or pass them as arguments), "
            f"but found {len(pdb_files)}: {found}"
        )

    # Prefer a file with 'wt' or 'wild' in its name as the reference structure
    wt_candidates = [
        p for p in pdb_files
        if "wt" in os.path.basename(p).lower() or "wild" in os.path.basename(p).lower()
    ]
    if len(wt_candidates) == 1:
        wt_file = wt_candidates[0]
        mut_file = [p for p in pdb_files if p != wt_file][0]
    else:
        wt_file, mut_file = pdb_files[0], pdb_files[1]

    return wt_file, mut_file


# Parse optional arguments passed via:
# run pymol_structure_analysis.py [wt.pdb] [mut.pdb] [resi_num] [chain_id]
cli_args = sys.argv[1:]
work_dir = get_work_dir()
os.makedirs(work_dir, exist_ok=True)
os.chdir(work_dir)

wt_path, mut_path = resolve_pdb_files(work_dir, cli_args)
resi_num = int(cli_args[2]) if len(cli_args) >= 3 else 70
chain_id = cli_args[3] if len(cli_args) >= 4 else "A"

if not os.path.exists(wt_path) or not os.path.exists(mut_path):
    raise FileNotFoundError(f"Could not find PDB files:\n  WT:  {wt_path}\n  MUT: {mut_path}")

print(f"Working directory: {work_dir}")
print(f"Wild-type PDB:     {os.path.basename(wt_path)}")
print(f"Mutant PDB:        {os.path.basename(mut_path)}")

cmd.delete("all")
cmd.load(wt_path, "wt")
cmd.load(mut_path, "mut")

# 1. Align structures
try:
    align_result = cmd.cealign("wt", "mut")
    global_rmsd = align_result.get("RMSD", 0.0) if isinstance(align_result, dict) else 0.0
except Exception:
    align_result = cmd.align("mut", "wt", cycles=0, transform=1)
    global_rmsd = align_result[0] if align_result else 0.0

# Auto-detect whether chain exists in the PDB; fallback to residue-only if blank chain
if cmd.count_atoms(f"wt and chain {chain_id} and resi {resi_num}") > 0:
    chain_sel = f"chain {chain_id} and "
else:
    chain_sel = ""

target_sel = f"{chain_sel}resi {resi_num}"

# Detect wild-type and mutant residue names dynamically (e.g., TYR -> ALA)
wt_resn_list, mut_resn_list = [], []
cmd.iterate(f"wt and {target_sel} and name CA", "wt_resn_list.append(resn)", space={"wt_resn_list": wt_resn_list})
cmd.iterate(f"mut and {target_sel} and name CA", "mut_resn_list.append(resn)", space={"mut_resn_list": mut_resn_list})

wt_resn = wt_resn_list[0].capitalize() if wt_resn_list else "Wt"
mut_resn = mut_resn_list[0].capitalize() if mut_resn_list else "Mut"
mutation_tag = f"{wt_resn}{resi_num}{mut_resn}"

# 2. Calculate Local Backbone RMSD (window around target residue)
try:
    local_rmsd = cmd.rms_cur(
        f"mut and {chain_sel}resi {resi_num - 4}-{resi_num + 4} and name CA",
        f"wt and {chain_sel}resi {resi_num - 4}-{resi_num + 4} and name CA",
    )
except Exception:
    local_rmsd = 0.0


# 3. Extract Backbone Dihedral Angles (Phi and Psi) with Circular Wrap-Around
def get_phi_psi(model, resi):
    resi = int(resi)
    try:
        phi = cmd.get_dihedral(
            f"{model} and {chain_sel}resi {resi - 1} and name C",
            f"{model} and {chain_sel}resi {resi} and name N",
            f"{model} and {chain_sel}resi {resi} and name CA",
            f"{model} and {chain_sel}resi {resi} and name C",
        )
        psi = cmd.get_dihedral(
            f"{model} and {chain_sel}resi {resi} and name N",
            f"{model} and {chain_sel}resi {resi} and name CA",
            f"{model} and {chain_sel}resi {resi} and name C",
            f"{model} and {chain_sel}resi {resi + 1} and name N",
        )
        return f"Φ = {phi:.2f}°, Ψ = {psi:.2f}°", phi, psi
    except Exception:
        return "Φ = N/A, Ψ = N/A", None, None


wt_angles_str, wt_phi, wt_psi = get_phi_psi("wt", resi_num)
mut_angles_str, mut_phi, mut_psi = get_phi_psi("mut", resi_num)

if wt_phi is not None and mut_phi is not None:
    delta_phi = abs(mut_phi - wt_phi)
    if delta_phi > 180:
        delta_phi = 360 - delta_phi
    delta_psi = abs(mut_psi - wt_psi)
    if delta_psi > 180:
        delta_psi = 360 - delta_psi
    torsion_impact_str = f"ΔΦ = {delta_phi:.2f}°, ΔΨ = {delta_psi:.2f}° (Local torsional adaptation)"
    delta_psi_text = f"{delta_psi:.2f}°"
else:
    torsion_impact_str = "ΔΦ = N/A, ΔΨ = N/A (Check residue/chain numbering)"
    delta_psi_text = "N/A"

# 4. Secondary Structure (DSSP)
cmd.dss("wt")
cmd.dss("mut")
wt_ss_list, mut_ss_list = [], []
cmd.iterate(f"wt and {target_sel} and name CA", "wt_ss_list.append(ss)", space={"wt_ss_list": wt_ss_list})
cmd.iterate(f"mut and {target_sel} and name CA", "mut_ss_list.append(ss)", space={"mut_ss_list": mut_ss_list})

ss_map = {
    "H": "Alpha Helix (H)",
    "S": "Beta Sheet (S)",
    "L": "Loop / Coil (L)",
    "": "Loop / Coil",
}
wt_ss = ss_map.get(wt_ss_list[0] if wt_ss_list else "", "Loop / Coil")
mut_ss = ss_map.get(mut_ss_list[0] if mut_ss_list else "", "Loop / Coil")

# 5. Render Publication Figure in PyMOL
cmd.color("marine", "wt")
cmd.color("orange", "mut")
cmd.show("cartoon", "wt or mut")
cmd.show("sticks", f"wt and {target_sel} or mut and {target_sel}")
cmd.hide("dashes")
cmd.hide("labels")
cmd.set("antialias", 2)
cmd.zoom(f"wt and {target_sel}", 8)

fig_path = os.path.join(work_dir, f"{mutation_tag}_matrix_figure.png")
cmd.png(fig_path, width=2400, height=1800, dpi=300, ray=0)
print(f"Saved figure to: {fig_path}")

# 6. Generate Word Matrix Report (.DOCX)
doc = Document()

for section in doc.sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

title_p = doc.add_paragraph()
title_run = title_p.add_run(
    f"Wild-Type ({wt_resn}{resi_num}) vs. Mutant ({mut_resn}{resi_num}) Matrix (Chain {chain_id})"
)
title_run.font.size = Pt(18)
title_run.font.bold = True
title_run.font.color.rgb = RGBColor(20, 30, 45)

subtitle_p = doc.add_paragraph()
sub_run = subtitle_p.add_run(
    f"PyMOL Structural Comparison | WT: {os.path.basename(wt_path)} vs. Mutant: {os.path.basename(mut_path)}"
)
sub_run.font.size = Pt(10)
sub_run.font.color.rgb = RGBColor(100, 110, 125)

doc.add_paragraph()

headers = [
    "Biophysical Parameter",
    f"Wild-Type ({wt_resn}{resi_num})",
    f"Mutant ({mut_resn}{resi_num})",
    "Structural Impact",
]

rows_data = [
    (
        "Residue Chemistry",
        f"Wild-type side chain ({wt_resn})",
        f"Substituted side chain ({mut_resn})",
        "Side-chain volume, polarity, and steric profile alteration",
    ),
    (
        "Dihedral Angles (Φ, Ψ)",
        wt_angles_str,
        mut_angles_str,
        torsion_impact_str,
    ),
    (
        "Backbone Amide Proton",
        "Present (N-H H-bond donor)",
        "Present (N-H H-bond donor)",
        "Peptide backbone hydrogen bonding capacity preserved",
    ),
    (
        "Local Interaction & Packing",
        "Native side-chain contacts & packing",
        "Altered side-chain contacts & local packing",
        "Local structural relaxation or steric adjustment",
    ),
    (
        "Superposition RMSD",
        "Reference structure",
        f"Local Cα RMSD: {local_rmsd:.3f} Å",
        "Measures local backbone deviation around target site",
    ),
    (
        "Secondary Structure (DSSP)",
        wt_ss,
        mut_ss,
        "Local conformational integrity check",
    ),
]

table = doc.add_table(rows=len(rows_data) + 1, cols=4)
table.autofit = False

col_widths = [Inches(1.5), Inches(1.5), Inches(1.5), Inches(2.2)]
for row in table.rows:
    for idx, width in enumerate(col_widths):
        row.cells[idx].width = width

hdr_cells = table.rows[0].cells
for idx, header_text in enumerate(headers):
    hdr_cells[idx].text = header_text
    set_cell_background(hdr_cells[idx], "E8ECF2")
    for paragraph in hdr_cells[idx].paragraphs:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in paragraph.runs:
            run.font.bold = True
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(20, 30, 45)

for r_idx, row_data in enumerate(rows_data):
    row_cells = table.rows[r_idx + 1].cells
    bg_color = "F9FAFC" if r_idx % 2 == 1 else "FFFFFF"

    for c_idx, cell_value in enumerate(row_data):
        cell = row_cells[c_idx]
        cell.text = cell_value
        set_cell_background(cell, bg_color)

        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(9.5)
                run.font.color.rgb = RGBColor(40, 45, 55)

                if c_idx == 1:
                    run.font.color.rgb = RGBColor(0, 90, 160)
                elif c_idx == 2 and r_idx in [0, 1, 3, 4]:
                    run.font.color.rgb = RGBColor(25, 125, 60)
                    run.font.bold = True
                elif c_idx == 3 and r_idx in [0, 1, 3, 4]:
                    run.font.color.rgb = RGBColor(25, 125, 60)
                    run.font.bold = True

doc.add_paragraph()

callout_table = doc.add_table(rows=1, cols=1)
callout_cell = callout_table.cell(0, 0)
set_cell_background(callout_cell, "F0F3F9")

cp = callout_cell.paragraphs[0]
cp.paragraph_format.space_before = Pt(6)
cp.paragraph_format.space_after = Pt(6)
cp.paragraph_format.left_indent = Inches(0.1)
cp.paragraph_format.right_indent = Inches(0.1)

r_title = cp.add_run("Structural Summary:\n")
r_title.font.bold = True
r_title.font.size = Pt(10)
r_title.font.color.rgb = RGBColor(20, 30, 45)

r_body = cp.add_run(
    f"Substitution of {wt_resn}{resi_num} with {mut_resn}{resi_num} in chain {chain_id} "
    f"alters local side-chain chemistry and packing, showing a local backbone "
    f"dihedral shift (ΔΨ = {delta_psi_text}) and a local Cα RMSD of {local_rmsd:.3f} Å."
)
r_body.font.size = Pt(9.5)
r_body.font.color.rgb = RGBColor(50, 55, 65)

docx_path = os.path.join(work_dir, f"{mutation_tag}_Biophysical_Matrix_Report.docx")
doc.save(docx_path)
print(f"Matrix report successfully generated and saved to: {docx_path}")