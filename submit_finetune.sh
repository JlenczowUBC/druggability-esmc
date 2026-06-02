#!/bin/bash
#SBATCH --job-name=druggability-finetune
#SBATCH --account=<YOUR_ALLOCATION_HERE>     # e.g. st-kilgore-1-gpu — fill in Dr. Kilgore's allocation
#SBATCH --partition=gpu_a100                  # adjust to whatever partition is available on Sockeye
#SBATCH --gres=gpu:1                          # request one GPU
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00                       # 4 hours; adjust if training needs longer
#SBATCH --output=logs/finetune_%j.out
#SBATCH --error=logs/finetune_%j.err

# ============================================================
# UBC Sockeye job script for ESM-C druggability fine-tuning
# ============================================================
# Submit with: sbatch submit_finetune.sh
# Monitor with: squeue -u $USER
# Cancel with: scancel <job_id>
# ============================================================

mkdir -p logs checkpoints

# Load required modules (adjust to whatever Sockeye provides)
module purge
module load gcc
module load cuda/12.2
module load miniconda3

# Activate the conda env
source activate druggability-esmc

# Print env info for debugging
echo "Job started: $(date)"
echo "Node: $(hostname)"
echo "CUDA devices: $CUDA_VISIBLE_DEVICES"
nvidia-smi
python -c "import torch; print('Torch:', torch.__version__, 'CUDA:', torch.cuda.is_available())"

# Run the notebook headless, save outputs in-place
jupyter nbconvert \
    --to notebook \
    --execute finetune.ipynb \
    --output finetune.ipynb \
    --ExecutePreprocessor.timeout=-1

echo "Job finished: $(date)"
