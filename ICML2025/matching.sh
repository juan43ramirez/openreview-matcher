# The matcher for ICML 2025 follows the following structure:
# * Aggregate the affinity scores
# * Filter out suspicious bids, and translate them into numeric fields
# * Compute one first matching assigning 3 reviewers to each submission
#    * This matching requires two constraints: conflicts and no first-time reviewers
# * Compute a second matching assigning a 4th reviewer to each submission
#    * Constraints: keep previous matching, conflicts, geographical diversity

# ----------------------------------------------------------------------------------
# Hyper-parameters
# ----------------------------------------------------------------------------------

export DATA_FOLDER="ICML2025/data"
export ASSIGNMENTS_FOLDER="ICML2025/assignments"

export QUANTILE=0.75
export UPWEIGHT_OR_PAPERS=True
export Q=0.5 # Upper bound on the marginal probability of each reviewer-paper pair being matched, for "Randomized" matcher

# ----------------------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------------------

# For the matcher
conda create -n openreview-matcher python=3.10
conda activate openreview-matcher
pip install .

# For other scripts
pip install pandas

# Assert all required files exist
# * $DATA_FOLDER/scores_with_origin.csv
# * $DATA_FOLDER/bids.csv
# * $DATA_FOLDER/constraints/conflict_constraints.csv
# * $DATA_FOLDER/constraints/first_time_reviewer_constraints.csv

echo "\nChecking required files..."
for file in $DATA_FOLDER/scores_with_origin.csv $DATA_FOLDER/bids.csv \
	$DATA_FOLDER/constraints/conflict_constraints.csv $DATA_FOLDER/constraints/first_time_reviewer_constraints.csv
do
	if [ ! -f $file ]; then
		echo "File $file does not exist."
		exit 1
	fi
done

echo "All required files exist."

# Create the output folder
mkdir -p $ASSIGNMENTS_FOLDER


# ----------------------------------------------------------------------------------
# Pre-processing
# ----------------------------------------------------------------------------------

# Aggregate affinity scores using the 0.75 quantile
python ICML2025/scripts/aggregate_scores.py \
	--input $DATA_FOLDER/scores_with_origin.csv \
	--output $DATA_FOLDER/aggregated_scores.csv \
	--quantile $QUANTILE \
	--reweight $UPWEIGHT_OR_PAPERS

# Filter out suspicious bids. TODO: implement
bash ICML2025/scripts/secure-paper-bidding.sh

# Translate bids into numeric fields
python ICML2025/scripts/translate_bids.py \
	--input $DATA_FOLDER/bids.csv \
	--output $DATA_FOLDER/numeric_bids.csv

# ---------------------------------------------------------------------------------
# Initial Matching of 3 reviewers per paper. The 4th reviewer is assigned later
# ---------------------------------------------------------------------------------

# This matching requires two sources of constraints:
# * $DATA_FOLDER/constraints/conflict_constraints.csv: [paper_id, reviewer_id, constraint]
# * $DATA_FOLDER/constraints/first_time_reviewer_constraints.csv: [paper_id, reviewer_id, constraint]

# For constraint files, the possible values for the constraint attribute are:
# * -1: conflict
# * 0: no effect
# * 1: forced assignment

# The matcher only accepts constraints in the form of a single CSV file, so we need to
# aggregate the constraints into a single file.
python ICML2025/scripts/join_conflicts.py \
	--files $DATA_FOLDER/constraints/conflict_constraints.csv \
		$DATA_FOLDER/constraints/first_time_reviewer_constraints.csv \
	--output $DATA_FOLDER/constraints/constraints_for_first_matching.csv

# Initial matching. This expects the following files:
# * $DATA_FOLDER/aggregated_scores.csv [paper_id, reviewer_id, score]
# * $DATA_FOLDER/numeric_bids.csv: [paper_id, reviewer_id, numeric_bid]

# The matcher computes and uses the following score:
# weight_1 * affinity_score + weight_2 * numeric_bid

python -m matcher \
	--scores $DATA_FOLDER/aggregated_scores.csv $DATA_FOLDER/numeric_bids.csv \
	--weights 1 1 \
	--constraints $DATA_FOLDER/constraints/constraints_for_first_matching.csv \
	--min_papers_default 0 \
	--max_papers_default 6 \
	--num_reviewers 3 \
	--num_alternates 1 \
	--solver Randomized \
	--probability_limits $Q

mv assignments.json $ASSIGNMENTS_FOLDER/first_matching.json

# Assignments in CSV format
python ICML2025/scripts/json_to_csv.py \
	--input $ASSIGNMENTS_FOLDER/first_matching.json \
	--output $ASSIGNMENTS_FOLDER/first_matching.csv

# ---------------------------------------------------------------------------------
# Second matching. Assign a 4th reviewer to each paper
# ---------------------------------------------------------------------------------

# Compute constraints based on the initial matching to ensure the first 2 reviewers
# assigned to a paper remain the same.
python ICML2025/scripts/extract_matching_constraints.py \
	--assignments $ASSIGNMENTS_FOLDER/first_matching.json \
	--output $DATA_FOLDER/constraints/constraints_after_matching.csv

# Compute constraints to ensure geographical diversity of reviewers. TODO: implement
python ICML2025/scripts/geographical_diversity.py \
	--assignments $ASSIGNMENTS_FOLDER/first_matching.csv \
	--output $DATA_FOLDER/constraints/geographical_constraints.csv

# Compute the constraints for the second matching.
python ICML2025/scripts/join_conflicts.py \
	--files $DATA_FOLDER/constraints/conflict_constraints.csv \
		$DATA_FOLDER/constraints/constraints_after_matching.csv \
		$DATA_FOLDER/constraints/geographical_constraints.csv \
	--output $DATA_FOLDER/constraints/constraints_for_second_matching.csv

# Run the matching with the new constraints.
python -m matcher \
	--scores $DATA_FOLDER/aggregated_scores.csv $DATA_FOLDER/numeric_bids.csv \
	--weights 1 1 \
	--constraints $DATA_FOLDER/constraints/constraints_for_second_matching.csv \
	--min_papers_default 0 \
	--max_papers_default 6 \
	--num_reviewers 4 \
	--num_alternates 1 \
	--solver Randomized \
	--probability_limits $Q

mv assignments.json $ASSIGNMENTS_FOLDER/second_matching.json

python ICML2025/scripts/json_to_csv.py \
	--input $ASSIGNMENTS_FOLDER/second_matching.json \
	--output $ASSIGNMENTS_FOLDER/second_matching.csv