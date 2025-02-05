#!/bin/bash
#SBATCH --reservation=ICML2025              # Reservation name
#SBATCH --output=/home/mila/j/juan.ramirez/output/%x-%j.out           # Output file
#SBATCH --error=/home/mila/j/juan.ramirez/output/%x-%j.err            # Error file
#SBATCH --time=2:00:00                     # Time limit hrs:min:sec
#SBATCH --ntasks=1                          # Number of tasks (cores)
#SBATCH --cpus-per-task=40			        # Number of CPUs per task
#SBATCH --mem=800GB                         # Memory limit
#SBATCH --mail-type=ALL                     # Email notifications
#SBATCH --mail-user=juan.ramirez@mila.quebec

module load anaconda
conda activate openreview-matcher

set -e  # Exit immediately if a command exits with a non-zero status

# Measure execution time and print in hours, minutes, and seconds
function print_time {
	local elapsed=$1
	printf "Elapsed time: %02d:%02d:%02d\n" $((elapsed/3600)) $((elapsed%3600/60)) $((elapsed%60))
}

start_time=$SECONDS


# ----------------------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------------------

if [ -z "$SLURM_JOB_NAME" ] && [ -z "$SLURM_JOB_ID" ]; then
    # Local execution (not running under SLURM or in an interactive session)
    export ROOT_FOLDER="ICML2025"
elif [ -z "$SLURM_JOB_NAME" ]; then
    # Interactive session
    export ROOT_FOLDER="$SCRATCH/ICML2025"
else
    # sbatch job
    export ROOT_FOLDER="$SCRATCH/ICML2025/jobs/$SLURM_JOB_ID"
fi

SCORES_FOLDER="$SCRATCH/ICML2025/scores" # folder with disaggregated score csv files

# ----------------------------------------------------------------------------------
# Aggregation hyper-parameters
# ----------------------------------------------------------------------------------

# # Max score: 1, 1, .55
# export OR_PAPER_WEIGHT=1 # Weight of OR papers in the aggregation of scores
# export QUANTILE=1 # Quantile to use for the aggregation of affinity scores
# export SCORES_NAME="aggregated_scores_max.csv"

# # Least conservative: .75, .5, .5
# export QUANTILE=0.75 # Quantile to use for the aggregation of affinity scores
# export OR_PAPER_WEIGHT=$(echo "1/0.5" | bc -l) # Weight of OR papers in the aggregation of scores
# export SCORES_NAME="least_conservative.csv"

# # Moderately conservative: .825, .7, .7
# export QUANTILE=0.825
# export OR_PAPER_WEIGHT=$(echo "1/0.7" | bc -l) # 1.43
# export SCORES_NAME="moderately_conservative.csv"

# # Most conservative: .9, .9, .9
# export QUANTILE=0.9
# export OR_PAPER_WEIGHT=$(echo "1/0.9" | bc -l) # 1.11
# export SCORES_NAME="most_conservative.csv"

# # Emphasizing randomization: .825, .7, .5
# export QUANTILE=0.825
# export OR_PAPER_WEIGHT=$(echo "1/0.7" | bc -l) # 1.43
# export SCORES_NAME="emphasizing_randomization.csv"

# # Emphasizing non-OR weight: .825, .5, .7
# export QUANTILE=0.825
# export OR_PAPER_WEIGHT=$(echo "1/0.5" | bc -l) # 2
# export SCORES_NAME="emphasizing_non_or_weight.csv"

# # Emphasizing quantiles: .75, .7, .7
# export QUANTILE=0.75
# export OR_PAPER_WEIGHT=$(echo "1/0.7" | bc -l) # 1.43
# export SCORES_NAME="emphasizing_quantiles.csv"

# ----------------------------------------------------------------------------------
# Aggregation
# ----------------------------------------------------------------------------------

# Aggregate affinity scores - If DEBUG, only the first chunk of the scores file is used
start_time=$SECONDS
python ICML2025/scripts/aggregate_scores.py \
	--scores_folder $SCORES_FOLDER \
	--output $ROOT_FOLDER/$SCORES_NAME \
	--quantile $QUANTILE \
	--or_weight $OR_PAPER_WEIGHT 
print_time $((SECONDS - start_time))