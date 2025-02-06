#!/bin/bash
#SBATCH --reservation=ICML2025              # Reservation name
#SBATCH --output=/home/mila/j/juan.ramirez/output/%x-%j.out           # Output file
#SBATCH --error=/home/mila/j/juan.ramirez/output/%x-%j.err            # Error file
#SBATCH --time=48:00:00                     # Time limit hrs:min:sec
#SBATCH --ntasks=1                          # Number of tasks (cores)
#SBATCH --cpus-per-task=10			        # Number of CPUs per task
#SBATCH --mem=150GB                         # Memory limit
#SBATCH --mail-type=ALL                     # Email notifications
#SBATCH --mail-user=juan.ramirez@mila.quebec

# Redirect stderr to stdout so both logs go to the same file
exec 2>&1

# ----------------------------------------------------------------------------------
# Outline of the matching process for ICML 2025 Reviewers
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

export GROUP="Reviewers"

export MAX_PAPERS=5 # Maximum number of papers each reviewer can review
export NUM_REVIEWS=4 # Number of reviewers per paper
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
mkdir -p $ASSIGNMENTS_FOLDER # create the output folder

# Assert required files exist
# * $SCRATCH/ICML2025/$GROUP/data/bids.csv
# * $SCRATCH/ICML2025/$GROUP/no_or_paper_reviewers.csv
# * $SCRATCH/ICML2025/$GROUP/emergency-4plus-reviewers.csv
# * $SCRATCH/ICML2025/$GROUP/reciprocal-reviewer-noBid.csv
# * $SCRATCH/ICML2025/$GROUP/colluders.csv
# * $SCRATCH/ICML2025/$GROUP/$SCORES_FILE

for file in $SCRATCH/ICML2025/$GROUP/data/bids.csv \
	$SCRATCH/ICML2025/$GROUP/no_or_paper_reviewers.csv \
	$SCRATCH/ICML2025/$GROUP/emergency-4plus-reviewers.csv \
	$SCRATCH/ICML2025/$GROUP/reciprocal-reviewer-noBid.csv \
	$SCRATCH/ICML2025/$GROUP/colluders.csv \
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
printf "\nMAX_PAPERS: $MAX_PAPERS"
printf "\nNUM_REVIEWS: $NUM_REVIEWS"
printf "\nMIN_POS_BIDS: $MIN_POS_BIDS"
printf "\nDEBUG: $DEBUG"
printf "\nROOT_FOLDER: $ROOT_FOLDER"
printf "\nDATA_FOLDER: $DATA_FOLDER"
printf "\nASSIGNMENTS_FOLDER: $ASSIGNMENTS_FOLDER"

# Copy data to the scratch folder
rsync -av --exclude 'archives' $SCRATCH/ICML2025/$GROUP/data/ $DATA_FOLDER

# Copy first-time reviewer constraints to DATA_FOLDER/constraints
mkdir -p $DATA_FOLDER/constraints
cp $SCRATCH/ICML2025/$GROUP/no_or_paper_reviewers.csv $DATA_FOLDER/constraints

# Copy emergency reviewers to the root folder - they are ignored in the matching
cp $SCRATCH/ICML2025/$GROUP/emergency-4plus-reviewers.csv $ROOT_FOLDER/emergency-4plus-reviewers.csv
cp $SCRATCH/ICML2025/$GROUP/reciprocal-reviewer-noBid.csv $ROOT_FOLDER/reciprocal-reviewer-noBid.csv

# Copy scores to the root folder
cp $SCRATCH/ICML2025/$GROUP/$SCORES_FILE $ROOT_FOLDER/scores.csv


# ----------------------------------------------------------------------------------
# Pre-process data
# ----------------------------------------------------------------------------------

printf "\n----------------------------------------"
printf "\nPre-processing data..."
printf "\n----------------------------------------\n"

# TODO: Filter out suspicious bids

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

# Remove emergency reviewers from scores, bids, and constraints. NOTE: this will
# overwrite the original files.
printf "\n----------------------------------------"
python ICML2025/scripts/exclude_reviewers.py \
	--exclude_reviewer_files $ROOT_FOLDER/emergency-4plus-reviewers.csv \
		$ROOT_FOLDER/reciprocal-reviewer-noBid.csv \
	--files $ROOT_FOLDER/scores.csv \
		$DATA_FOLDER/filtered_bids.csv \
		$DATA_FOLDER/constraints/conflict_constraints.csv


# ---------------------------------------------------------------------------------
# Initial Matching of 3 reviewers per paper
# ---------------------------------------------------------------------------------

# Remove first-time reviewers from scores, bids, and constraints for the initial
# matching only. Will produce new files with the prefix "first_matching_".
printf "\n----------------------------------------"
python ICML2025/scripts/remove_first_time_reviewers.py \
	--no_or_paper_reviewers $DATA_FOLDER/no_or_paper_reviewers.csv \
	--scores $ROOT_FOLDER/scores.csv \
	--bids $DATA_FOLDER/filtered_bids.csv \
	--constraints $DATA_FOLDER/constraints/conflict_constraints.csv \
	--output_prefix first_matching

# Matching
printf "\n----------------------------------------"
printf "\nStarting first matching..."
printf "\n----------------------------------------\n"

start_time=$SECONDS
python -m matcher \
	--scores $ROOT_FOLDER/first_matching_scores.csv $DATA_FOLDER/first_matching_bids.csv \
	--weights 1 1 \
	--constraints $DATA_FOLDER/constraints/first_matching_constraints.csv \
	--min_papers_default 0 \
	--max_papers_default $MAX_PAPERS \
	--num_reviewers $(($NUM_REVIEWS - 1)) \
	--solver Randomized \
	--allow_zero_score_assignments \
	--probability_limits $Q \
	--output_folder $ASSIGNMENTS_FOLDER

mv $ASSIGNMENTS_FOLDER/assignments.json $ASSIGNMENTS_FOLDER/first_matching.json
mv $ASSIGNMENTS_FOLDER/alternates.json $ASSIGNMENTS_FOLDER/first_matching_alternates.json
print_time $((SECONDS - start_time))

# Convert assignments JSON to CSV for convenience
python ICML2025/scripts/json_to_csv.py \
	--input $ASSIGNMENTS_FOLDER/first_matching.json \
	--output $ASSIGNMENTS_FOLDER/first_matching.csv

# Convert alternates JSON to CSV for convenience
python ICML2025/scripts/json_to_csv.py \
	--input $ASSIGNMENTS_FOLDER/first_matching_alternates.json \
	--output $ASSIGNMENTS_FOLDER/first_matching_alternates.csv

# ---------------------------------------------------------------------------------
# Second matching. Assign a 4th reviewer to each paper
# ---------------------------------------------------------------------------------

# Extract the number of papers each reviewer can review in the second matching as
# MAX_PAPERS - number of papers assigned in the first matching
printf "\n----------------------------------------"
python ICML2025/scripts/reviewer_supply_after_matching.py \
	--assignments $ASSIGNMENTS_FOLDER/first_matching.json \
	--max_papers $MAX_PAPERS \
	--supply_output $DATA_FOLDER/constraints/reviewer_supply_after_matching.csv \
	--exhausted_reviewers_output $DATA_FOLDER/exhausted_reviewers.csv \
	--remaining_reviewer_constraints_output $DATA_FOLDER/constraints/remaining_reviewer_constraints.csv
print_time $((SECONDS - start_time))

# Extract geographical diversity constraints
printf "\n----------------------------------------"
python ICML2025/scripts/geographical_diversity.py \
	--assignments $ASSIGNMENTS_FOLDER/first_matching.csv \
	--output $DATA_FOLDER/constraints/geographical_constraints.csv
print_time $((SECONDS - start_time))

# Remove emergency reviewers and reviewers without more reviews left before the
# second matching.
printf "\n----------------------------------------"
python ICML2025/scripts/exclude_reviewers.py \
	--exclude_reviewer_files $ROOT_FOLDER/emergency-4plus-reviewers.csv \
		$ROOT_FOLDER/reciprocal-reviewer-noBid.csv \
		$DATA_FOLDER/exhausted_reviewers.csv \
	--files $ROOT_FOLDER/scores.csv \
		$DATA_FOLDER/filtered_bids.csv \
		$DATA_FOLDER/constraints/conflict_constraints.csv \
		$DATA_FOLDER/constraints/geographical_constraints.csv \
		$DATA_FOLDER/constraints/reviewer_supply_after_matching.csv

# If in DEBUG mode, subsample the new constraints. Will overwrite the original files.
if [ "$DEBUG" = "True" ]; then
	printf "\n----------------------------------------"
	python ICML2025/scripts/subsample.py \
	--scores $ROOT_FOLDER/scores.csv \
	--files $DATA_FOLDER/constraints/reviewer_supply_after_matching.csv \
		$DATA_FOLDER/constraints/geographical_constraints.csv \
		$DATA_FOLDER/constraints/remaining_reviewer_constraints.csv
fi

# Join constraints into a single file
printf "\n----------------------------------------"
python ICML2025/scripts/join_constraints.py \
	--files $DATA_FOLDER/constraints/conflict_constraints.csv \
		$DATA_FOLDER/constraints/geographical_constraints.csv \
		$DATA_FOLDER/constraints/remaining_reviewer_constraints.csv \
	--output $DATA_FOLDER/constraints/constraints_for_second_matching.csv
print_time $((SECONDS - start_time))

# Matching
printf "\n----------------------------------------"
printf "\nStarting second matching..."
printf "\n----------------------------------------\n"

start_time=$SECONDS
python -m matcher \
	--scores $ROOT_FOLDER/scores.csv $DATA_FOLDER/filtered_bids.csv \
	--weights 1 1 \
	--constraints $DATA_FOLDER/constraints/constraints_for_second_matching.csv \
	--min_papers_default 0 \
	--max_papers_default $MAX_PAPERS \
	--max_papers $DATA_FOLDER/constraints/reviewer_supply_after_matching.csv \
	--num_reviewers 1 \
	--num_alternates 1 \
	--solver Randomized \
	--allow_zero_score_assignments \
	--probability_limits $Q \
	--output_folder $ASSIGNMENTS_FOLDER

mv $ASSIGNMENTS_FOLDER/assignments.json $ASSIGNMENTS_FOLDER/second_matching.json
mv $ASSIGNMENTS_FOLDER/alternates.json $ASSIGNMENTS_FOLDER/second_matching_alternates.json
print_time $((SECONDS - start_time))

# Convert assignments JSON to CSV for convenience
python ICML2025/scripts/json_to_csv.py \
	--input $ASSIGNMENTS_FOLDER/second_matching.json \
	--output $ASSIGNMENTS_FOLDER/second_matching.csv

# Convert alternates JSON to CSV for convenience
python ICML2025/scripts/json_to_csv.py \
	--input $ASSIGNMENTS_FOLDER/second_matching_alternates.json \
	--output $ASSIGNMENTS_FOLDER/second_matching_alternates.csv

# ---------------------------------------------------------------------------------
printf "\n----------------------------------------"

# Join first and second matching assignments
python ICML2025/scripts/join_assignments.py \
	--files $ASSIGNMENTS_FOLDER/first_matching.csv \
		$ASSIGNMENTS_FOLDER/second_matching.csv \
	--output $ASSIGNMENTS_FOLDER/final_assignments.csv

printf "\nDone."
printf "\nSCORES_FILE: $SCORES_FILE"
printf "\nAssignments saved in $ASSIGNMENTS_FOLDER"

print_time $((SECONDS - start_time))