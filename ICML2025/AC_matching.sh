#!/bin/bash
#SBATCH --reservation=ICML2025              # Reservation name
#SBATCH --output=/home/mila/j/juan.ramirez/output/%x-%j.out           # Output file
#SBATCH --error=/home/mila/j/juan.ramirez/output/%x-%j.err            # Error file
#SBATCH --time=24:00:00                     # Time limit hrs:min:sec
#SBATCH --ntasks=1                          # Number of tasks (cores)
#SBATCH --cpus-per-task=10			        # Number of CPUs per task
#SBATCH --mem=150GB                         # Memory limit
#SBATCH --mail-type=ALL                     # Email notifications
#SBATCH --mail-user=juan.ramirez@mila.quebec

# Redirect stderr to stdout so both logs go to the same file
exec 2>&1

# ----------------------------------------------------------------------------------
# Outline of the matching process for ICML 2025 Area Chairs
# * Aggregate Affinity Scores
# * Pre-process bids
# * Initial Matching of 3 reviewers per paper, with the following constraints:
#   * Conflicts
#   * No first-time reviewers
# * Second Matching. Assign a 4th reviewer to each paper, with the following constraints:
#   * Conflicts
#   * Geographical diversity
#   * Enforce the previous matching of 3 reviewers per paper
# ----------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------------------

# # For the matcher
# module load anaconda
# conda create -n openreview-matcher python=3.10
# conda activate openreview-matcher
# pip install .

# # For other scripts
# pip install pandas tqdm openreview-py dask pyarrow

module load anaconda
conda activate openreview-matcher

# ----------------------------------------------------------------------------------
# NOTE: the OpenReview matcher requires a Gurobi license.
# ----------------------------------------------------------------------------------

set -e  # Exit immediately if a command exits with a non-zero status

# Measure execution time and print in hours, minutes, and seconds
function print_time {
	local elapsed=$1
	printf "Elapsed time: %02d:%02d:%02d\n" $((elapsed/3600)) $((elapsed%3600/60)) $((elapsed%60))
}

start_time=$SECONDS

# ----------------------------------------------------------------------------------
# Hyper-parameters
# ----------------------------------------------------------------------------------

export DEBUG=False # Used to subsample submission and reviewer data

export MIN_POS_BIDS=20 # minimum number of positive bids in order to take them into account
export QUANTILE=0.75 # Quantile to use for the aggregation of affinity scores
export OR_PAPER_WEIGHT=1.5 # Weight of OR papers in the aggregation of scores
export Q=0.5 # Upper bound on the marginal probability of each reviewer-paper pair being matched, for "Randomized" matcher

export OPENREVIEW_USERNAME=''
export OPENREVIEW_PASSWORD=''


if [ -z "$SLURM_JOB_NAME" ] && [ -z "$SLURM_JOB_ID" ]; then
    # Local execution (not running under SLURM or in an interactive session)
    export ROOT_FOLDER="ICML2025"
    export DATA_FOLDER="ICML2025/data"
    export ASSIGNMENTS_FOLDER="ICML2025/assignments"
elif [ -z "$SLURM_JOB_NAME" ]; then
    # Interactive session
    export ROOT_FOLDER="$SCRATCH/ICML2025"
    export DATA_FOLDER="$SCRATCH/ICML2025/data"
    export ASSIGNMENTS_FOLDER="$SCRATCH/ICML2025/assignments"
else
    # sbatch job
    export ROOT_FOLDER="$SCRATCH/ICML2025/jobs/$SLURM_JOB_ID"
    export DATA_FOLDER="$SCRATCH/ICML2025/jobs/$SLURM_JOB_ID/data"
    export ASSIGNMENTS_FOLDER="$SCRATCH/ICML2025/jobs/$SLURM_JOB_ID/assignments"
fi

mkdir -p $ROOT_FOLDER # create the scores folder
mkdir -p $DATA_FOLDER # create the data folder
mkdir -p $ASSIGNMENTS_FOLDER # create the output folder

SCORES_FOLDER="$SCRATCH/ICML2025/scores" # folder with disaggregated score csv files

# Copy data to the scratch folder
rsync -av --exclude 'archives' $HOME/github/openreview-expertise/ICML2025/data/ $DATA_FOLDER

# Assert required files exist
# * $DATA_FOLDER/bids.csv

printf "\nChecking required files..."
for file in $DATA_FOLDER/bids.csv
do
	if [ ! -f $file ]; then
		printf "File $file does not exist."
		exit 1
	fi
done
print_time $((SECONDS - start_time))
printf "All required files exist."

# ----------------------------------------------------------------------------------
# Pre-processing
# ----------------------------------------------------------------------------------

# Aggregate affinity scores - If DEBUG, only the first chunk of the scores file is used
python ICML2025/scripts/aggregate_scores.py \
	--scores_folder $SCORES_FOLDER \
	--output $ROOT_FOLDER/aggregated_scores.csv \
	--quantile $QUANTILE \
	--or_weight $OR_PAPER_WEIGHT 
print_time $((SECONDS - start_time))

# Filter out bids from reviewers that do not have at least 20 positive bids
python ICML2025/scripts/filter_bids.py \
	--input $DATA_FOLDER/bids.csv \
	--output $DATA_FOLDER/filtered_bids.csv \
	--min-pos-bids $MIN_POS_BIDS
print_time $((SECONDS - start_time))

# Prepare conflict constraints
python ICML2025/scripts/fetch_conflict_constraints.py \
	--match_group Area_Chairs \
	--output $DATA_FOLDER/constraints/conflict_constraints.csv

# If in DEBUG mode, subsample the scores, bids, and constraints. Will overwrite the
# original files.
if [ "$DEBUG" = "True" ]; then
	python ICML2025/scripts/subsample.py \
	--scores $ROOT_FOLDER/aggregated_scores.csv \
	--files $DATA_FOLDER/filtered_bids.csv \
		$DATA_FOLDER/constraints/conflict_constraints.csv
fi

# ---------------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------------

# Matching
printf "\n----------------------------------------"
printf "\nStarting first matching..."
printf "\n----------------------------------------\n"

start_time=$SECONDS
python -m matcher \
	--scores $ROOT_FOLDER/aggregated_scores.csv $DATA_FOLDER/bids.csv \
	--weights 1 1 \
	--constraints $DATA_FOLDER/constraints/conflict_constraints.csv \
	--min_papers_default 0 \
	--max_papers_default 10 \
	--num_reviewers 1 \
	--solver Randomized \
	--allow_zero_score_assignments \
	--probability_limits $Q \
	--output_folder $ASSIGNMENTS_FOLDER

mv $ASSIGNMENTS_FOLDER/assignments.json $ASSIGNMENTS_FOLDER/ac_matching.json
print_time $((SECONDS - start_time))

# Convert assignments JSON to CSV
python ICML2025/scripts/json_to_csv.py \
	--input $ASSIGNMENTS_FOLDER/ac_matching.json \
	--output $ASSIGNMENTS_FOLDER/ac_matching.csv
print_time $((SECONDS - start_time))