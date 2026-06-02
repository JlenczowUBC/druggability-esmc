"""
Convert phase1_dataset.xlsx into druggability_dataset.csv with the schema
the fine-tuning notebook expects.

Usage:
    python scripts/convert_dataset.py path/to/phase1_dataset.xlsx data/druggability_dataset.csv

The xlsx is expected to have at least these columns (case-insensitive matching):
    uniprot_id, gene_symbol, sequence, length, fda_flag, chembl_flag, druggable

Column names from the original notebook (Uniprot_ID, FDA_flag, ChEMBL_flag, etc.)
are auto-renamed below.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd


COLUMN_RENAMES = {
    "Uniprot_ID": "uniprot_id",
    "uniprot_id": "uniprot_id",
    "UniProt_ID": "uniprot_id",
    "Gene_Symbol": "gene_symbol",
    "gene_symbol": "gene_symbol",
    "Sequence": "sequence",
    "sequence": "sequence",
    "Length": "length",
    "length": "length",
    "FDA_flag": "fda_flag",
    "fda_flag": "fda_flag",
    "ChEMBL_flag": "chembl_flag",
    "chembl_flag": "chembl_flag",
    "druggable": "druggable",
    "Druggable": "druggable",
}

REQUIRED = {"uniprot_id", "sequence", "druggable"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_xlsx", help="Path to phase1_dataset.xlsx")
    parser.add_argument("output_csv", help="Path to write the CSV")
    args = parser.parse_args()

    in_path = Path(args.input_xlsx)
    out_path = Path(args.output_csv)

    if not in_path.exists():
        sys.exit(f"Input file not found: {in_path}")

    print(f"Reading {in_path}")
    df = pd.read_excel(in_path)
    print(f"  shape: {df.shape}")
    print(f"  columns: {list(df.columns)}")

    df = df.rename(columns={c: COLUMN_RENAMES[c] for c in df.columns if c in COLUMN_RENAMES})

    missing = REQUIRED - set(df.columns)
    if missing:
        sys.exit(f"Missing required columns: {missing}\nFound: {list(df.columns)}")

    keep = [c for c in ["uniprot_id", "gene_symbol", "sequence", "length",
                        "fda_flag", "chembl_flag", "druggable"] if c in df.columns]
    df = df[keep]

    df = df.dropna(subset=["uniprot_id", "sequence", "druggable"])
    df["druggable"] = df["druggable"].astype(int)
    if "length" in df.columns:
        df["length"] = df["length"].astype(int)
    if "fda_flag" in df.columns:
        df["fda_flag"] = df["fda_flag"].fillna(0).astype(int)
    if "chembl_flag" in df.columns:
        df["chembl_flag"] = df["chembl_flag"].fillna(0).astype(int)

    print(f"  rows after cleanup: {len(df):,}")
    print(f"  positive (druggable=1): {int(df['druggable'].sum()):,}")
    print(f"  negative (druggable=0): {int((1 - df['druggable']).sum()):,}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
