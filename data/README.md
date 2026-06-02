# Dataset Documentation

## File

`druggability_dataset.csv` (~3 MB) — used by `finetune.ipynb`. Contains UniProt IDs, sequences, and binary druggability labels for 3,853 human proteins.

## Schema

| Column | Type | Description |
|---|---|---|
| `uniprot_id` | string | UniProt accession (e.g. `P00533`) |
| `gene_symbol` | string | HUGO gene symbol (e.g. `EGFR`) |
| `sequence` | string | Amino acid sequence in one-letter code |
| `length` | int | Sequence length in residues |
| `fda_flag` | int (0/1) | 1 if the protein is the target of an FDA-approved drug |
| `chembl_flag` | int (0/1) | 1 if any compound binds at IC50/Ki/Kd ≤ 100 nM in ChEMBL |
| `druggable` | int (0/1) | `fda_flag OR chembl_flag` — the supervised label |

## How the labels were assigned

| Source | Used as | Notes |
|---|---|---|
| `protein_class_FDA.tsv` | Positive label source | 851 unique UniProt IDs, FDA-approved drug targets (Pharos-derived, Tclin equivalent). |
| `protein_class_potential.tsv` | Excluded from negative pool | 1,757 UniProt IDs, proteins under active drug development. Excluded so they don't get mislabeled as non-druggable. |
| UniProt REST API | Sequence + negative sampling | 20,431 reviewed human proteins. Pool for sampling negatives. |
| ChEMBL REST API | Positive label source | Each protein checked against ChEMBL. `chembl_flag = 1` if any compound has IC50, Ki, or Kd ≤ 100 nM in nanomolar units on a single-protein target. |

## Final composition

| Subset | Count | % |
|---|---|---|
| FDA + ChEMBL (strongest positives) | 519 | 13.5% |
| FDA only (clinical evidence) | 334 | 8.7% |
| ChEMBL only (preclinical evidence) | 270 | 7.0% |
| Non-druggable (neither) | 2,730 | 70.8% |
| **Total** | **3,853** | **100%** |

Druggable: 1,123 (29.2%). Non-druggable: 2,730 (70.8%). Roughly 2.4:1 class imbalance.

## Honest caveats

**1. The negative label is weak.** "Not in DrugBank or ChEMBL at 100 nM" doesn't strictly mean "not druggable" — it often just means "understudied." Some negatives are likely mislabeled positives that nobody has tested yet.

**2. Family leakage.** Top 10 gene-name prefixes in the positive class are all well-known target families:

| Prefix | Family | Count |
|---|---|---|
| CACN | calcium channels | 26 |
| GABR | GABA receptors | 16 |
| HDAC | histone deacetylases | 11 |
| SLC1 | solute carriers | 11 |
| CHRN | nicotinic receptors | 11 |
| KCNJ | inward potassium channels | 10 |
| PRKC | protein kinase C | 9 |
| ATP2 | ATPases | 8 |
| KCNA | voltage potassium channels | 8 |
| SLC2 | solute carriers | 8 |

Random train/test splits put close relatives in both folds, which inflates AUC. Sequence-similarity-based splits (e.g. MMseqs2 clustering at 30-50% identity) are the proper fix — planned future work.

**3. ChEMBL cutoff.** The 100 nM threshold is strict — it captures only high-affinity binders. Looser thresholds (1 μM) would expand the positive class but at the cost of label quality. Worth exploring as a sensitivity analysis.

## Reproducing the dataset

The full dataset build lives in a separate notebook (`phase1_dataset.ipynb`, not in this repo). Briefly:

1. Read `protein_class_FDA.tsv` to get 851 positive UniProt IDs.
2. Read `protein_class_potential.tsv` to get 1,757 exclusion IDs.
3. Query UniProt for all 20,431 reviewed human proteins.
4. Sample 3,000 random negatives from the proteome minus FDA + exclusion lists (seed 42).
5. Fetch sequences for FDA + negatives.
6. Query ChEMBL REST API for each protein with `CHEMBL_CUTOFF_NM = 100`.
7. Set `druggable = fda_flag OR chembl_flag`.

To convert from the original xlsx to this CSV format, use `scripts/convert_dataset.py`.
