#!/usr/bin/env python3
"""
Parse Gaussian output (.fchk, .out, .log) to extract HOMO/LUMO information.
Automatically determines orbital indices, energies, and HOMO-LUMO gap.

Usage:
  python parse_mo.py input.fchk
  python parse_mo.py input.out
  python parse_mo.py input.log
"""

import re
import sys
from pathlib import Path


def parse_fchk(path):
    """Parse formatted checkpoint file for orbital info."""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Get number of alpha electrons
    m = re.search(r'Number of alpha electrons\s+I\s+(\d+)', content)
    if not m:
        # Try total electrons
        m = re.search(r'Number of electrons\s+I\s+(\d+)', content)
        if not m:
            print("[ERROR] Cannot find electron count in fchk")
            return None, None, None, None
        n_electrons = int(m.group(1))
        # Assume closed shell: n_alpha = n_electrons // 2
        n_alpha = n_electrons // 2
    else:
        n_alpha = int(m.group(1))
    
    # Get number of beta electrons
    m = re.search(r'Number of beta electrons\s+I\s+(\d+)', content)
    if m:
        n_beta = int(m.group(1))
    else:
        n_beta = n_alpha
    
    # Determine if restricted (closed shell)
    restricted = (n_alpha == n_beta)
    
    # Get orbital energies
    m = re.search(r'Alpha Orbital Energies\s+R\s+N=\s+(\d+)', content)
    if not m:
        print("[ERROR] Cannot find Alpha Orbital Energies in fchk")
        return None, None, None, None
    
    n_orbitals = int(m.group(1))
    
    # Find the energy values - they start on the lines after the header
    idx = content.find('Alpha Orbital Energies')
    lines = content[idx:].split('\n')
    
    energies = []
    in_energies = False
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        # Stop when we hit another section (text without numbers)
        if re.match(r'^[A-Z]', line) and not re.search(r'[-+]?\d', line):
            break
        # Skip lines that are just headers/labels
        if re.match(r'^[A-Za-z]', line) and not re.search(r'[-+]?\d', line):
            break
        # Extract energy values
        values = re.findall(r'[-+]?\d+\.\d+E[+-]\d+', line)
        if not values:
            values = re.findall(r'[-+]?\d\.\d+E[+-]\d+', line)
        energies.extend(values)
    
    if len(energies) < n_alpha:
        print(f"[ERROR] Only found {len(energies)} energies, expected at least {n_alpha}")
        return None, None, None, None
    
    # HOMO = n_alpha (1-indexed), LUMO = n_alpha + 1
    homo_idx = n_alpha
    lumo_idx = n_alpha + 1
    
    if lumo_idx > len(energies):
        print(f"[ERROR] LUMO index {lumo_idx} exceeds energy list length {len(energies)}")
        return None, None, None, None
    
    homo_e = float(energies[homo_idx - 1])
    lumo_e = float(energies[lumo_idx - 1])
    
    gap_au = lumo_e - homo_e
    gap_ev = gap_au * 27.2114
    
    return homo_idx, lumo_idx, homo_e, lumo_e, gap_au, gap_ev, restricted


def parse_out(path):
    """Parse Gaussian .out/.log file for orbital info."""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Check for Normal termination
    if 'Normal termination' not in content:
        print("[WARN] Gaussian output does not show Normal termination")
    
    # Find occupied/virtual orbital count
    # Look for "Occupied" or count alpha electrons
    n_alpha = None
    n_beta = None
    
    # Try to find from population analysis section
    m = re.search(r'alpha electrons\s+(\d+)', content)
    if not m:
        m = re.search(r'(\d+)\s+alpha electrons', content)
    if m:
        n_alpha = int(m.group(1))
    
    m = re.search(r'beta\s+electrons\s+(\d+)', content)
    if not m:
        m = re.search(r'(\d+)\s+beta\s+electrons', content)
    if m:
        n_beta = int(m.group(1))
    
    if n_alpha is None:
        print("[WARN] Cannot determine electron count from .out file. Try .fchk instead.")
        return None, None, None, None
    
    if n_beta is None:
        n_beta = n_alpha
    
    restricted = (n_alpha == n_beta)
    homo_idx = n_alpha
    lumo_idx = n_alpha + 1
    
    # Parse orbital energies from output
    # Look for "Alpha  occ. eigenvalues" or similar patterns
    energies = []
    
    # Try to find orbital energies (in .out format)
    # Pattern: lines with orbital index and energy
    for pattern in [
        r'Alpha\s+occ\.\s+eigenvalues',
        r'Alpha\s+MO\s+eigenvalues',
        r'Population analysis',
    ]:
        idx = content.find(pattern)
        if idx >= 0:
            # Extract energies from following lines
            block = content[idx:idx+5000]
            energies = re.findall(r'[-+]?\d+\.\d{5}', block)
            break
    
    if not energies:
        print("[WARN] Could not parse orbital energies from .out. Try .fchk instead.")
        print(f"HOMO index: {homo_idx}, LUMO index: {lumo_idx}")
        return homo_idx, lumo_idx, None, None, None, None, restricted
    
    if len(energies) < lumo_idx:
        print(f"[WARN] Only found {len(energies)} energies, need at least {lumo_idx}")
        return homo_idx, lumo_idx, None, None, None, None, restricted
    
    homo_e = float(energies[homo_idx - 1])
    lumo_e = float(energies[lumo_idx - 1])
    gap_au = lumo_e - homo_e
    gap_ev = gap_au * 27.2114
    
    return homo_idx, lumo_idx, homo_e, lumo_e, gap_au, gap_ev, restricted


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_mo.py <file.fchk|file.out|file.log>")
        sys.exit(1)
    
    path = sys.argv[1]
    if not Path(path).exists():
        print(f"[ERROR] File not found: {path}")
        sys.exit(1)
    
    ext = Path(path).suffix.lower()
    
    if ext in ['.fchk', '.fch']:
        result = parse_fchk(path)
    elif ext in ['.out', '.log']:
        result = parse_out(path)
    else:
        print(f"[ERROR] Unsupported file type: {ext}. Use .fchk, .out, or .log")
        sys.exit(1)
    
    if result[0] is None:
        sys.exit(1)
    
    homo_idx, lumo_idx, homo_e, lumo_e, gap_au, gap_ev, restricted = result
    
    print(f"=== {Path(path).name} ===")
    print(f"System: {'Closed-shell' if restricted else 'Open-shell'}")
    print(f"HOMO: orbital {homo_idx}", end="")
    if homo_e is not None:
        print(f", energy = {homo_e:.6f} Hartree = {homo_e*27.2114:.3f} eV")
    else:
        print()
    print(f"LUMO: orbital {lumo_idx}", end="")
    if lumo_e is not None:
        print(f", energy = {lumo_e:.6f} Hartree = {lumo_e*27.2114:.3f} eV")
    else:
        print()
    if gap_ev is not None:
        print(f"HOMO-LUMO Gap: {gap_au:.6f} Hartree = {gap_ev:.3f} eV")


if __name__ == "__main__":
    main()
