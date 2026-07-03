#!/usr/bin/env python3
"""
Check and fix Gaussian .gjf input files for HOMO/LUMO MO calculation.
Route: .gjf -> Gaussian -> .chk -> formchk -> .fchk -> Multiwfn

Usage:
  python check_gjf.py input.gjf                    # Check only
  python check_gjf.py input.gjf --fix              # Check and auto-fix
  python check_gjf.py input.gjf --fix --dry-run    # Show what would change
"""

import argparse
import re
import sys
from pathlib import Path


# Required standard for HOMO/LUMO MO calculation
STD_FUNCTIONAL = "b3lyp"
STD_BASIS = "6-311+g(d,p)"

# All keywords that must be present in route section
REQUIRED_KEYWORDS = ["opt", "freq", "pop=full"]


def read_gjf(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def find_route_line(lines):
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("#p") or s.startswith("#"):
            return i, s
    return None, None


def find_chk_line(lines):
    for i, line in enumerate(lines):
        if line.strip().startswith("%chk="):
            return i, line.strip()
    return None, None


def find_charge_mult_line(lines):
    for i, line in enumerate(lines):
        if re.match(r"^-?\d+\s+\d+$", line.strip()):
            return i
    return None


def get_molecule_name(path):
    return Path(path).stem


def parse_route_level(route_line):
    """Extract functional/basis from route line like '#p b3lyp/6-311+g(d,p) opt'.
    Returns (functional, basis) or (None, None) if not parseable."""
    # Strip leading # or #p
    stripped = re.sub(r'^#p?\s*', '', route_line.strip().lower())
    # Try to match functional/basis pattern
    m = re.match(r'(\S+)/(\S+)', stripped)
    if m:
        return m.group(1), m.group(2)
    return None, None


def check_gjf(path):
    lines = read_gjf(path)
    missing = []
    present = []
    level_issues = []

    route_idx, route_line = find_route_line(lines)
    if route_line is None:
        print("[ERROR] No route section (#p ...) found!")
        return None, lines

    # Check #p
    if route_line.strip().startswith("#p"):
        present.append("#p")
    else:
        missing.append("#p")

    # Check keyword presence
    route_lower = route_line.lower()
    for kw in REQUIRED_KEYWORDS:
        if kw.lower() in route_lower:
            present.append(kw)
        else:
            missing.append(kw)

    # Check functional/basis level
    func, basis = parse_route_level(route_line)
    if func and basis:
        func_ok = func == STD_FUNCTIONAL
        basis_ok = basis == STD_BASIS.lower()
        if func_ok and basis_ok:
            present.append(f"{STD_FUNCTIONAL}/{STD_BASIS}")
        else:
            level_issues.append(f"functional: {func} -> {STD_FUNCTIONAL}" if not func_ok else None)
            level_issues.append(f"basis: {basis} -> {STD_BASIS}" if not basis_ok else None)
            level_issues = [x for x in level_issues if x]
            missing.append(f"{STD_FUNCTIONAL}/{STD_BASIS} (current: {func}/{basis})")
    else:
        missing.append(f"{STD_FUNCTIONAL}/{STD_BASIS} (unparseable)")

    # Check %chk
    chk_idx, chk_line = find_chk_line(lines)
    if chk_line:
        expected_chk = f"%chk={get_molecule_name(path)}.chk"
        if chk_line.lower() != expected_chk.lower():
            present.append("%chk (name mismatch, will fix)")
            missing.append("%chk")
        else:
            present.append("%chk")
    else:
        missing.append("%chk")

    # Check charge/mult
    cm_idx = find_charge_mult_line(lines)
    if cm_idx is not None:
        present.append("charge/mult")
    else:
        missing.append("charge/mult")

    return (present, missing, route_idx, route_line, lines)


def fix_gjf(path, dry_run=False):
    result = check_gjf(path)
    if result is None:
        return
    present, missing, route_idx, route_line, lines = result

    if not missing:
        return lines, []

    name = get_molecule_name(path)
    changes = []

    # Rebuild route section
    new_route = route_line

    # Fix #p
    if "#p" in missing:
        new_route = re.sub(r'^#\s+', '#p ', new_route)
        if not new_route.startswith("#p"):
            new_route = "#p " + re.sub(r'^#\s*', '', new_route)
        changes.append("+ #p")
    elif not new_route.strip().startswith("#p"):
        new_route = "#p " + re.sub(r'^#\s*', '', new_route)

    # Fix functional/basis level: replace with standard
    func, basis = parse_route_level(route_line)
    if func and basis and (func != STD_FUNCTIONAL or basis.lower() != STD_BASIS.lower()):
        old_pattern = f"{func}/{basis}"
        new_pattern = f"{STD_FUNCTIONAL}/{STD_BASIS}"
        new_route = new_route.replace(old_pattern, new_pattern)
        changes.append(f"+ {old_pattern} -> {new_pattern}")
    elif not func:
        # Can't parse level, prepend standard
        new_route = re.sub(r'^(#p\s+)', f'\\1{STD_FUNCTIONAL}/{STD_BASIS} ', new_route)
        changes.append(f"+ {STD_FUNCTIONAL}/{STD_BASIS}")

    # Fix keywords: strip and re-add opt, freq (clean rebuild)
    new_route = re.sub(r'\bopt\b', '', new_route, flags=re.IGNORECASE)
    new_route = re.sub(r'\bfreq\b', '', new_route, flags=re.IGNORECASE)
    new_route = re.sub(r'\s+', ' ', new_route).strip()
    # Always add opt and freq back
    new_route += " opt freq"
    changes.append("+ opt freq")

    # Clean up: remove geom=connectivity (not needed with opt+freq)
    new_route = re.sub(r'\bgeom=connectivity\b', '', new_route, flags=re.IGNORECASE)
    new_route = re.sub(r'\s+', ' ', new_route).strip()

    lines[route_idx] = new_route + "\n"

    # Fix %chk
    if "%chk" in missing:
        lines = [l for l in lines if not l.strip().startswith("%chk=")]
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("%"):
                insert_pos = i + 1
            else:
                break
        lines.insert(insert_pos, f"%chk={name}.chk\n")
        changes.append(f"+ %chk={name}.chk")

    return lines, changes


def main():
    parser = argparse.ArgumentParser(
        description="Check and fix Gaussian .gjf for HOMO/LUMO MO calculation"
    )
    parser.add_argument("gjf", help="Path to .gjf file")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show changes without writing")
    args = parser.parse_args()

    gjf_path = Path(args.gjf)
    if not gjf_path.exists():
        print(f"[ERROR] File not found: {gjf_path}")
        sys.exit(1)

    result = check_gjf(gjf_path)
    if result is None:
        sys.exit(1)

    present, missing, route_idx, route_line, lines = result

    print(f"=== {gjf_path.name} ===")
    print(f"Route: {route_line}")
    print()

    print("Status:")
    for kw in present:
        print(f"  [OK] {kw}")
    for kw in missing:
        print(f"  [MISS] {kw}")

    if missing and (args.fix or args.dry_run):
        fixed_lines, changes = fix_gjf(gjf_path, dry_run=args.dry_run)
        if args.dry_run:
            print()
            print("Dry-run - would apply:")
            for c in changes:
                print(f"  {c}")
        else:
            with open(gjf_path, "w", encoding="utf-8") as f:
                f.writelines(fixed_lines)
            print()
            print("Applied fixes:")
            for c in changes:
                print(f"  {c}")
            print(f"[OK] {gjf_path} updated.")
    elif missing:
        print()
        print("Run with --fix to auto-correct.")
    else:
        print()
        print("[OK] All checks passed. Ready for Gaussian.")
        print(f"Next: g16 < {gjf_path.name} > {get_molecule_name(gjf_path)}.out")


if __name__ == "__main__":
    main()

