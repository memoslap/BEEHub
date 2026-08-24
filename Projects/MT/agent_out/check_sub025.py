#!/usr/bin/env python3
"""Check sub-025 ses-01 for conversion/parsing issues."""
import csv, os
from collections import Counter

def read_tsv(path):
    """Read TSV, stripping BOM if present."""
    with open(path) as f:
        raw = f.readline()
    if raw.startswith("﻿"):
        raw = raw[1:]
    header = raw.strip().split("\t")
    with open(path) as f:
        f.readline()
        rows = []
        for line in f:
            cols = line.strip().split("\t")
            if len(cols) == len(header):
                rows.append(dict(zip(header, cols)))
    return rows

def cnt_to_dict(c):
    """Safely convert Counter to dict (handles non-string keys)."""
    return dict(sorted(c.items(), key=lambda x: (x[0] if isinstance(x[0], str) else int(x[0]))))

# sub-025 ses-01 source and derivative
s25_src = read_tsv(
    "/media/Data03/Studies/Research_BEEHub/Git_repository/BEEHub/Projects/MT/bids_data/sub-025/ses-01/beh/sub-025_ses-01_task-gonogo_beh.tsv"
)
s25_der = read_tsv(
    "/media/Data03/Studies/Research_BEEHub/Git_repository/BEEHub/Projects/MT/derivatives/stopping/sub-025/ses-01/beh/sub-025_ses-01_task-gonogo_desc-stopping_beh.tsv"
)
s20_der = read_tsv(
    "/media/Data03/Studies/Research_BEEHub/Git_repository/BEEHub/Projects/MT/derivatives/stopping/sub-020/ses-01/beh/sub-020_ses-01_task-gonogo_desc-stopping_beh.tsv"
)

print("=== sub-025 ses-01 ===")
print(f"Source rows: {len(s25_src)}")
s25_go = [r for r in s25_src if r["trial_type"] == "go"]
s25_nogo = [r for r in s25_src if r["trial_type"] == "nogo"]
print(f"  go: {len(s25_go)}, nogo: {len(s25_nogo)}")

blk_go = Counter(r["block_number"] for r in s25_go)
blk_nogo = Counter(r["block_number"] for r in s25_nogo)
print(f"  go by block: {cnt_to_dict(blk_go)}")
print(f"  nogo by block: {cnt_to_dict(blk_nogo)}")

src_correct = Counter(r.get("correct", "?") for r in s25_go)
print(f"  source correct: {cnt_to_dict(src_correct)}")

print(f"\nDerivative rows: {len(s25_der)}")
s25d_go = [r for r in s25_der if r["trial_type"] == "go"]
s25d_nogo = [r for r in s25_der if r["trial_type"] == "nogo"]
print(f"  go: {len(s25d_go)}, nogo: {len(s25d_nogo)}")

s25d_acc = Counter(r["accuracy"] for r in s25d_go)
print(f"  der accuracy: {cnt_to_dict(s25d_acc)}")

s25d_nogo_out = Counter(r["nogo_outcome"] for r in s25d_nogo)
print(f"  nogo outcomes: {cnt_to_dict(s25d_nogo_out)}")

s25d_wrong = [r for r in s25d_go if r["accuracy"] == "0"]
print(f"\n  {len(s25d_wrong)} go trials classified as incorrect")
for col in ["go_first_left_inside", "parse_failed_time", "any_click"]:
    vals = Counter(r[col] for r in s25d_wrong)
    print(f"    {col}: {cnt_to_dict(vals)}")

# Compare with sub-020
print("\n=== sub-020 ses-01 (typical) ===")
s20_go = [r for r in s20_der if r["trial_type"] == "go"]
s20_acc = Counter(r["accuracy"] for r in s20_go)
print(f"  go: {len(s20_go)}")
print(f"  der accuracy: {cnt_to_dict(s20_acc)}")
s20_wrong = [r for r in s20_go if r["accuracy"] == "0"]
print(f"  {len(s20_wrong)} incorrect go trials")

# Source vs Derivative for sub-025
print("\n=== Source vs Derivative for sub-025 ses-01 ===")
s25_src_by_idx = {int(r["trial_index"]): r for r in s25_src}

s25d_wrong_idx = [int(r["trial_index"]) for r in s25d_go if r["accuracy"] == "0"]
s25d_correct_idx = [int(r["trial_index"]) for r in s25d_go if r["accuracy"] == "1"]

src_wrong_correct = [s25_src_by_idx.get(idx, {}).get("correct", "?") for idx in s25d_wrong_idx]
print(f"  Derivative accuracy=0 — source 'correct': {cnt_to_dict(Counter(src_wrong_correct))}")

src_correct_vals = [s25_src_by_idx.get(idx, {}).get("correct", "?") for idx in s25d_correct_idx]
print(f"  Derivative accuracy=1 — source 'correct': {cnt_to_dict(Counter(src_correct_vals))}")

if s25d_wrong_idx:
    print(f"\n  Sample wrong trial (idx={min(s25d_wrong_idx)}):")
    sample = s25_src_by_idx.get(min(s25d_wrong_idx))
    if sample:
        for k in ["trial_type", "block_number", "digit", "correct", "correct_response"]:
            if k in sample:
                print(f"    {k}: {sample[k]}")

# Parse failures
parse_fails = [r for r in s25_der if r.get("parse_failed_time") == "1"]
print(f"\n  Parse failures: {len(parse_fails)}")
for pf in parse_fails[:3]:
    print(f"    idx={pf['trial_index']} tt={pf['trial_type']} pf_time={pf['parse_failed_time']}")

# Source file check
raw_src = "/media/Data03/Studies/Research_BEEHub/Git_repository/BEEHub/Projects/MT/sourcedata/raw/25a_go_nogo_dm_2025-05-16_09h04.08.233.csv"
print(f"\n=== Source CSV ===")
print(f"  Exists: {os.path.exists(raw_src)}")
print(f"  Size: {os.path.getsize(raw_src):,} bytes")
with open(raw_src) as f:
    raw_lines = f.readlines()
    header_cols = raw_lines[0].strip().split(",")
    tt_count = sum(1 for line in raw_lines[1:] if line.strip())
    print(f"  CSV rows (incl header): {len(raw_lines)}")
    print(f"  Non-empty rows: {tt_count}")
    print(f"  First 10 cols: {[c.strip() for c in header_cols[:10]]}")

# Check header order for sub-025
print(f"\n=== Header order check ===")
# There are 2 header orders across files. Check which group sub-025 falls into.
print(f"  sub-025 BIDS header: {list(s25_src[0].keys())[:8]}...")
# Check if click_pos_x/y come before or after response_box_clicked
h = list(s25_src[0].keys())
try:
    rbc_idx = h.index("response_box_clicked")
    cpx_idx = h.index("click_pos_x")
    print(f"  response_box_clicked={rbc_idx}, click_pos_x={cpx_idx}")
    print(f"  Order: click_pos BEFORE response_box = {cpx_idx < rbc_idx}")
except ValueError:
    print(f"  Columns missing: check header")
