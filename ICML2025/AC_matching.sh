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
# * Aggregate Affinity Scores (see aggregate_scores.sh)
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

# -------------------------------- Edit these variables --------------------------------

export DEBUG=False # Used to subsample submission and reviewer data


# # Max score: 1, 1, .55
# export Q=.55 # Upper bound on the marginal probability of each reviewer-paper pair being matched, for "Randomized" matcher
# export SCORES_FILE=aggregated_scores_max.csv

# # Least conservative: .75, .5, .55
# export Q=0.55
# export SCORES_FILE=least_conservative.csv

# # Moderately conservative: .825, .7, .7
# export Q=0.7
# export SCORES_FILE=moderately_conservative.csv

# # Most conservative: .9, .9, .9
# export Q=0.9
# export SCORES_FILE=most_conservative.csv

# # Emphasizing randomization: .825, .7, .55
# export Q=0.55
# export SCORES_FILE=emphasizing_randomization.csv

# # Emphasizing non-OR weight: .825, .5, .7
# export Q=0.7
# export SCORES_FILE=emphasizing_non_or_weight.csv

# # Emphasizing quantiles: .75, .7, .7
# export Q=0.7
# export SCORES_FILE=emphasizing_quantiles.csv

export OPENREVIEW_USERNAME=''
export OPENREVIEW_PASSWORD=''

# ---------------------------- Do not edit these variables ----------------------------

export GROUP="Area_Chairs"

export MIN_PAPERS=6 # Minimum number of papers to assign to each reviewer
export MAX_PAPERS=12 # Maximum number of papers to assign to each reviewer
export MIN_POS_BIDS=10 # minimum number of positive bids in order to take them into account

if [ -z "$SLURM_JOB_NAME" ] && [ -z "$SLURM_JOB_ID" ]; then
    # Local execution (not running under SLURM or in an interactive session)
    export ROOT_FOLDER="ICML2025/$GROUP"
    export DATA_FOLDER="ICML2025/$GROUP/data"
    export ASSIGNMENTS_FOLDER="ICML2025/$GROUP/assignments"
elif [ -z "$SLURM_JOB_NAME" ]; then
    # Interactive session
    export ROOT_FOLDER="$SCRATCH/ICML2025/$GROUP"
    export DATA_FOLDER="$SCRATCH/ICML2025/$GROUP/data"
    export ASSIGNMENTS_FOLDER="$SCRATCH/ICML2025/$GROUP/assignments"
else
    # sbatch job
    export ROOT_FOLDER="$SCRATCH/ICML2025/$GROUP/jobs/$SLURM_JOB_ID"
    export DATA_FOLDER="$SCRATCH/ICML2025/$GROUP/jobs/$SLURM_JOB_ID/data"
    export ASSIGNMENTS_FOLDER="$SCRATCH/ICML2025/$GROUP/jobs/$SLURM_JOB_ID/assignments"
fi

mkdir -p $ROOT_FOLDER # create the scores folder
mkdir -p $DATA_FOLDER # create the data folder
mkdir -p $DATA_FOLDER/constraints # create the constraints folder
mkdir -p $ASSIGNMENTS_FOLDER # create the output folder

# Assert required files exist
# * $SCRATCH/ICML2025/$GROUP/data/bids.csv
# * $SCRATCH/ICML2025/$GROUP/exclude.csv
# * $SCRATCH/ICML2025/$GROUP/$SCORES_FILE

for file in $SCRATCH/ICML2025/$GROUP/data/bids.csv \
	$SCRATCH/ICML2025/$GROUP/exclude.csv \
	$SCRATCH/ICML2025/$GROUP/$SCORES_FILE
do
	if [ ! -f $file ]; then
		echo "File $file does not exist."
		exit 1
	fi
done

printf "All required files exist."

printf "\n----------------------------------------"
printf "\nStarting matching..."
printf "\n----------------------------------------\n"

print_time $((SECONDS - start_time))

printf "\nHyper-parameters:"
printf "\n----------------------------------------"
printf "\nSCORES_FILE: $SCORES_FILE"
printf "\nQ: $Q"
printf "\nMIN_PAPERS: $MIN_PAPERS"
printf "\nMAX_PAPERS: $MAX_PAPERS"
printf "\nNUM_REVIEWS: 1"
printf "\nMIN_POS_BIDS: $MIN_POS_BIDS"
printf "\nDEBUG: $DEBUG"
printf "\nROOT_FOLDER: $ROOT_FOLDER"
printf "\nDATA_FOLDER: $DATA_FOLDER"
printf "\nASSIGNMENTS_FOLDER: $ASSIGNMENTS_FOLDER"

# Copy data to the scratch folder
rsync -av --exclude 'archives' $SCRATCH/ICML2025/$GROUP/data/ $DATA_FOLDER

# Copy area chairs to exclude
cp $SCRATCH/ICML2025/$GROUP/exclude.csv $ROOT_FOLDER/exclude.csv

# Copy scores to the root folder
cp $SCRATCH/ICML2025/$GROUP/$SCORES_FILE $ROOT_FOLDER/scores.csv


# ----------------------------------------------------------------------------------
# Pre-process data
# ----------------------------------------------------------------------------------

printf "\n----------------------------------------"
printf "\nPre-processing data..."
printf "\n----------------------------------------\n"


# Filter out bids from reviewers that do not have at least MIN_POS_BIDS positive bids
python ICML2025/scripts/filter_bids.py \
	--input $DATA_FOLDER/bids.csv \
	--output $DATA_FOLDER/filtered_bids.csv \
	--min-pos-bids $MIN_POS_BIDS
print_time $((SECONDS - start_time))

# Prepare conflict constraints
printf "\n----------------------------------------"
python ICML2025/scripts/fetch_conflict_constraints.py \
	--match_group $GROUP \
	--output $DATA_FOLDER/constraints/conflict_constraints.csv

# If in DEBUG mode, subsample the scores, bids, and constraints. Will overwrite the
# original files.
if [ "$DEBUG" = "True" ]; then
	printf "\n----------------------------------------"
	python ICML2025/scripts/subsample.py \
	--scores $ROOT_FOLDER/scores.csv \
	--files $DATA_FOLDER/filtered_bids.csv \
		$DATA_FOLDER/constraints/conflict_constraints.csv
fi

# Remove some area chairs from the matching
printf "\n----------------------------------------"
python ICML2025/scripts/exclude_reviewers.py \
	--exclude_reviewer_files $ROOT_FOLDER/exclude.csv \
	--files $ROOT_FOLDER/scores.csv \
		$DATA_FOLDER/filtered_bids.csv \
		$DATA_FOLDER/constraints/conflict_constraints.csv


# ---------------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------------

# Matching
printf "\n----------------------------------------"
printf "\nStarting first matching..."
printf "\n----------------------------------------\n"

start_time=$SECONDS
python -m matcher \
	--scores $ROOT_FOLDER/scores.csv $DATA_FOLDER/filtered_bids.csv \
	--weights 1 1 \
	--constraints $DATA_FOLDER/constraints/conflict_constraints.csv \
	--min_papers_default 6 \
	--max_papers_default 12 \
	--num_reviewers 1 \
	--solver Randomized \
	--allow_zero_score_assignments \
	--probability_limits $Q \
	--output_folder $ASSIGNMENTS_FOLDER
print_time $((SECONDS - start_time))

# Convert assignments JSON to CSV for convenience
python ICML2025/scripts/json_to_csv.py \
	--input $ASSIGNMENTS_FOLDER/assignments.json \
	--output $ASSIGNMENTS_FOLDER/assignments.csv

# Convert alternates JSON to CSV for convenience
python ICML2025/scripts/json_to_csv.py \
	--input $ASSIGNMENTS_FOLDER/alternates.json \
	--output $ASSIGNMENTS_FOLDER/alternates.csv
print_time $((SECONDS - start_time))