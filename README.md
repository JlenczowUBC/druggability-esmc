# Druggability Prediction with ESM-C and LoRA Fine-Tuning

LoRA fine-tuning pipeline for predicting protein druggability from amino acid sequence using ESM-C 300M.

Part of the AI for Biochemistry directed studies project under Dr. Henry Kilgore at UBC. This repo contains the labeled dataset and a LoRA fine-tuning notebook that adapts ESM-C 300M for binary druggability classification.

## Background

Built a labeled dataset of 3,853 human proteins from FDA-approved drug targets and ChEMBL bioactivity data. Phase 1 of the project ran a frozen-embedding layer analysis with ESM-2 8M (best AUC 0.815 at layer 6, vs length-only baseline 0.615). This repo is Phase 2 — fine-tuning ESM-C 300M end-to-end with LoRA to push performance further.

## Repo contents

```
druggability-esm2/
├── README.md                         # this file
├── environment.yml                   # conda environment spec
├── finetune.ipynb                    # main fine-tuning notebook
├── submit_finetune.sh                # SLURM script for UBC Sockeye
├── data/
│   ├── druggability_dataset.csv      # 3,853 proteins, binary labels (~3 MB)
│   └── README.md                     # dataset documentation
├── scripts/
│   └── convert_dataset.py            # converts source xlsx to the CSV format used here
├── docs/
│   └── handoff.docx                  # full project context
├── .gitignore
└── LICENSE
```

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/<username>/druggability-esm2.git
cd druggability-esm2
```

### 2. Create the conda environment

```bash
conda env create -f environment.yml
conda activate druggability-esmc
```

This installs Python 3.11, PyTorch, transformers, peft (for LoRA), and the rest of the ML stack.

### 3. Verify GPU access

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"
```

You should see `True 1` (or higher) on a GPU node. Fine-tuning ESM-C 300M requires a real CUDA GPU. CPU-only machines can step through the early cells but training is infeasible without GPU.

### 4. Run the notebook

```bash
jupyter notebook finetune.ipynb
```

Or for headless execution on Sockeye, see the SLURM section below.

## Running on UBC Sockeye

A SLURM submission script is included:

```bash
sbatch submit_finetune.sh
```

The script requests one GPU node, loads the conda environment, and executes the full notebook to completion via `jupyter nbconvert`. Edit `submit_finetune.sh` to point at your Sockeye allocation and adjust walltime/partition as needed before submitting.

## Dataset

`data/druggability_dataset.csv` — 3,853 human proteins with columns `uniprot_id`, `gene_symbol`, `sequence`, `length`, `fda_flag`, `chembl_flag`, `druggable`. See `data/README.md` for full provenance.

Positives (1,123) are proteins with either FDA-approved drug targets or active ChEMBL bioactivity at ≤100 nM. Negatives (2,730) are randomly sampled from the human proteome with FDA-approved targets and Pharos potential targets excluded to reduce label noise.

## What the fine-tuning notebook does

Adapts Dr. Kilgore's ESM-C LoRA template (`esmc_finetune.ipynb`) for binary druggability classification. Main differences from the original template:

- Binary task instead of multi-class enzyme classification (`num_labels=1`, BCE loss)
- Reads `druggability_dataset.csv` instead of the CARE enzyme CSV
- Stratified train/dev/test split (70/15/15) preserving the ~29% positive class ratio
- Reports AUC in addition to accuracy (standard for imbalanced binary classification)
- Saves the best checkpoint by dev AUC, then evaluates on the held-out test split

LoRA configuration follows the original template (rank 8, alpha 16, target modules and parameters matching ESM-C's architecture). Only LoRA adapters and the new classification head are trained — the ESM-C backbone stays frozen.

## Expected outputs

After running the notebook end to end:

- Training loss + accuracy curves
- Dev AUC at each checkpoint (every 250 steps by default)
- Final test AUC and confusion matrix
- Best LoRA adapter weights saved to `checkpoints/best/`

## Honest caveats

**1. Family leakage.** The dataset uses random train/test splitting, but druggable proteins are dominated by a few well-known target families (kinases, GPCRs, ion channels). Related family members appear in both train and test, inflating performance estimates. The proper fix is sequence-similarity-based clustering with MMseqs2; that's planned future work.

**2. Compute requirements.** ESM-C 300M needs a real GPU. 1,000 training steps takes ~4 minutes on an H100 per Dr. Kilgore's original notebook. Expect longer on lesser GPUs.

**3. Dataset size.** 3,853 proteins is small for fine-tuning a 300M parameter model. LoRA helps by only training ~0.1% of parameters, but dataset expansion (Open Targets tractability buckets, Pharos full development levels, tiered ChEMBL thresholds) is the next planned step.

## Citation

If this code or dataset is useful, please cite the underlying ESM-C work:

```
ESM Cambrian: Revealing the mysteries of proteins with unsupervised learning
EvolutionaryScale Team. 2024.
```

## Contact

Joseph Lenczowski — UBC undergraduate, directed studies under Dr. Henry Kilgore.
