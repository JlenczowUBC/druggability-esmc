# Druggability Prediction with ESM-C and LoRA Fine-Tuning

LoRA fine-tuning pipeline for predicting protein druggability from amino acid sequence using ESM-C 300M.

## Background

Built a labeled dataset of 3,853 human proteins from FDA-approved drug targets and ChEMBL bioactivity data. Phase 1 of the project ran a frozen-embedding layer analysis with ESM-2 8M (best AUC 0.815 at layer 6, vs length-only baseline 0.615). This repo is Phase 2 — fine-tuning ESM-C 300M end-to-end with LoRA to push performance further.

## Repo contents

```
druggability-esm2/
├── README.md                         # this file
├── environment.yml                   # conda environment spec
├── finetune.ipynb                    # main fine-tuning notebook (single code cell)
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
git clone https://github.com/JlenczowUBC/druggability-esmc.git
cd druggability-esmc
```

### 2. Create the conda environment

```bash
conda env create -f environment.yml
conda activate druggability-esmc
```

This installs Python 3.12, CUDA-enabled PyTorch, transformers, peft (for LoRA), Biohub's native esm package, and the rest of the ML stack.

### 3. Verify GPU access

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"
```

You should see `True 1` (or higher) on a GPU node. Fine-tuning ESM-C 300M requires a real CUDA GPU.

### 4. Run the notebook

```bash
jupyter notebook finetune.ipynb
```

The notebook is consolidated into a single code cell so the entire pipeline runs with one Shift+Enter (or via `nbconvert --execute` for headless runs). Section markers as comments inside the cell separate the original stages: imports and configuration, dataset loading and stratified splits, ESMC model setup, LoRA, training, evaluation, and prediction export.

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

Adapts an ESM-C LoRA template for binary druggability classification. Pipeline:

- Loads ESMC-300M weights from HuggingFace Hub via `snapshot_download`, then patches the native esm loader to find them
- Wraps the raw ESMC backbone in a custom `ESMCForBinaryClassification` module that mean-pools residue embeddings and adds a one-logit classification head with `binary_cross_entropy_with_logits` loss
- Reads `druggability_dataset.csv` and produces a stratified train/dev/test split (70/15/15) preserving the ~29% positive class ratio
- Wraps the model with LoRA (rank 8, alpha 16) targeting `out_proj` modules, with a graceful fallback to classifier-head-only training if LoRA can't attach
- Trains with AdamW, autocast bfloat16 on CUDA, periodic dev evaluation with best-checkpoint saving by dev AUC
- Reports AUC alongside accuracy (standard for imbalanced binary classification)
- Outputs `binary_classifier_predictions.csv` in `outputs/` with per-sequence predicted probabilities

## Expected outputs

After running the notebook end to end:

- Training loss + accuracy curves
- Dev AUC at each checkpoint (every 250 steps by default)
- Final test AUC and confusion matrix
- Best model state saved to `checkpoints/best/model_state.pt`
- `outputs/binary_classifier_predictions.csv` with per-protein predicted probabilities

## Citation

If this code or dataset is useful, please cite the underlying ESM-C work:

```
ESM Cambrian: Revealing the mysteries of proteins with unsupervised learning
EvolutionaryScale Team. 2024.
```
