#!/usr/bin/env python3
"""
Generate Gaussian .gjf input file for ESP calculation.

Usage:
  python generate_esp_input.py --name benzene --charge 0 --mult 1 --xyz benzene.xyz
  python generate_esp_input.py --name molecule --charge 0 --mult 1 --smiles "c1ccccc1"
"""

import argparse
import sys
from pathlib import Path


def make_gjf(name, charge, mult, coords_block, functional="b3lyp",
             basis="6-311+g(d,p)", dispersion="gd3bj", mem="8GB", nproc=8,
             calc_type="opt", extra_keywords=None):
    """Generate a Gaussian .gjf input string for ESP calculation.

    Args:
        name: Molecule name / job title
        charge: Net charge
        mult: Spin multiplicity (1=singlet, 2=doublet, 3=triplet)
        coords_block: Multi-line string of atomic coordinates (Element X Y Z)
        functional: DFT functional (default b3lyp)
        basis: Basis set (default 6-311+g(d,p))
        dispersion: Dispersion correction (gd3bj, gd3, or empty for none)
        mem: Memory allocation
        nproc: Number of processors
        calc_type: "opt" for optimization, "sp" for single-point
        extra_keywords: Additional Gaussian keywords string

    Returns:
        String content of the .gjf file
    """
    route = "#p"

    if calc_type == "opt":
        route += " opt freq"
    elif calc_type == "sp":
        pass
    elif calc_type == "freq":
        route += " opt freq"
    else:
        print(f"[WARN] Unknown calc_type '{calc_type}', defaulting to sp")
        calc_type = "sp"

    route += f" {functional}/{basis}"

    if dispersion:
        route += f" empiricaldispersion={dispersion}"

    # No output=wfn — use formchk to convert .chk to .fchk instead

    if extra_keywords:
        route += f" {extra_keywords}"

    lines = [
        f"%chk={name}.chk",
        f"%mem={mem}",
        f"%nprocshared={nproc}",
        route,
        "",
        f"{name} ESP calculation",
        "",
        f"{charge} {mult}",
        coords_block.strip(),
        "",
        "",  # No .wfn line needed
        "",
    ]

    return "\n".join(lines)


def parse_xyz(xyz_path):
    """Parse a standard .xyz file, return (comment, coords_block)."""
    with open(xyz_path, "r") as f:
        lines = f.readlines()

    n_atoms = int(lines[0].strip())
    comment = lines[1].strip() if len(lines) > 1 else ""
    coords = "".join(lines[2:2 + n_atoms])

    return comment, coords


def main():
    parser = argparse.ArgumentParser(
        description="Generate Gaussian .gjf for ESP calculation"
    )
    parser.add_argument("--name", required=True, help="Molecule name")
    parser.add_argument("--charge", type=int, required=True, help="Net charge")
    parser.add_argument("--mult", type=int, required=True, help="Spin multiplicity")
    parser.add_argument("--xyz", help="Path to .xyz coordinate file")
    parser.add_argument("--smiles", help="SMILES string (requires openbabel or rdkit)")
    parser.add_argument("--functional", default="b3lyp", help="DFT functional")
    parser.add_argument("--basis", default="6-311+g(d,p)", help="Basis set")
    parser.add_argument("--dispersion", default="gd3bj",
                        help="Dispersion (gd3bj/gd3/none)")
    parser.add_argument("--mem", default="8GB", help="Memory")
    parser.add_argument("--nproc", type=int, default=8, help="Processors")
    parser.add_argument("--calc", default="opt",
                        choices=["opt", "sp", "freq"],
                        help="Calculation type")
    parser.add_argument("--extra", help="Extra Gaussian keywords")
    parser.add_argument("--output", help="Output .gjf path (default: <name>.gjf)")

    args = parser.parse_args()

    if args.dispersion.lower() == "none":
        args.dispersion = ""

    # Get coordinates
    if args.xyz:
        comment, coords = parse_xyz(args.xyz)
    elif args.smiles:
        print("[ERROR] SMILES conversion not available without OpenBabel/RDKit.")
        print("Install openbabel and run: obabel -ismi -oxyz --gen3d")
        sys.exit(1)
    else:
        print("[ERROR] Provide --xyz or --smiles")
        sys.exit(1)

    gjf_content = make_gjf(
        name=args.name,
        charge=args.charge,
        mult=args.mult,
        coords_block=coords,
        functional=args.functional,
        basis=args.basis,
        dispersion=args.dispersion,
        mem=args.mem,
        nproc=args.nproc,
        calc_type=args.calc,
        extra_keywords=args.extra,
    )

    output_path = args.output or f"{args.name}.gjf"
    Path(output_path).write_text(gjf_content)

    print(f"[OK] Written {output_path}")
    print()
    print("Next steps in ESP workflow:")
    print(f"  1. g16 < {output_path} > {args.name}.log")
    print(f"  2. formchk {args.name}.chk {args.name}.fchk")
    print(f"  3. Multiwfn ESPiso.bat  -> VMD visualize")


if __name__ == "__main__":
    main()