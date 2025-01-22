# The matcher for ICML 2025 follows the following structure:
# * Aggregate the affinity scores
# * Filter out suspicious bids, and translate them into numeric fields
# * Compute one first matching assigning 2 reviewers to each submission
#    * This matching requires two constraints: conflicts and no first-time reviewers
# * Compute a second matching assigning a third reviewer to each submission
#    * Constraints: keep previous matching, conflicts
# * Third matching
#    * Constraints: keep previous matching, geographical diversity

# ----------------------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------------------

# For the matcher
conda create -n openreview-matcher python=3.10
conda activate openreview-matcher
pip install .

# For other scripts
pip install pandas

# ----------------------------------------------------------------------------------
# Hyper-parameters
# ----------------------------------------------------------------------------------

export DATA_FOLDER="ICML2025/data"
export ASSIGNMENTS_FOLDER="ICML2025/assignments"

export QUANTILE=0.75
export UPWEIGHT_OR_PAPERS=True
export Q=0.5 # Upper bound on the marginal probability of each reviewer-paper pair being matched, for "Randomized" matcher

# ----------------------------------------------------------------------------------
# Pre-processing
# ----------------------------------------------------------------------------------

# Aggregate affinity scores using the 0.75 quantile
python -m affinity \
	--input $DATA_FOLDER/scores_with_origin.csv \
	--output $DATA_FOLDER/aggregated_scores.csv \
	--quantile $QUANTILE \
	--reweight $UPWEIGHT_OR_PAPERS

# Filter out suspicious bids. TODO: implement and document
bash ICML2025/scripts/secure-paper-bidding.sh

# ---------------------------------------------------------------------------------
# Initial Matching of 2 reviewers per paper. The 3rd and 4th reviewers are assigned later
# ---------------------------------------------------------------------------------

# This matching requires two sources of constraints, which need to be aggregated for the matcher:
# * $DATA_FOLDER/constraints/conflict_constraints.csv: [paper_id, reviewer_id, constraint]
# * $DATA_FOLDER/constraints/first_time_reviewer_constraints.csv: [paper_id, reviewer_id, constraint]

# For constraint files, the possible values for the constraint attribute are:
# * -1: conflict
# * 0: no effect
# * 1: forced assignment

# Aggregate constraints.
python ICML2025/scripts/join_conflicts.py \
	--file1 $DATA_FOLDER/constraints/conflict_constraints.csv \
	--file2 $DATA_FOLDER/constraints/first_time_reviewer_constraints.csv \
	--output $DATA_FOLDER/constraints/constraints_for_first_matching.csv

# Initial matching. This expects the following files:
# * $DATA_FOLDER/aggregated_scores.csv [paper_id, reviewer_id, score]
# * $DATA_FOLDER/numeric_bids.csv: [paper_id, reviewer_id, numeric_bid]

python -m matcher \
	--scores $DATA_FOLDER/aggregated_scores.csv $DATA_FOLDER/numeric_bids.csv \
	--weights 1 1 \
	--constraints $DATA_FOLDER/constraints/constraints_for_first_matching.csv \
	--min_papers_default 0 \
	--max_papers_default 6 \
	--num_reviewers 2 \
	--num_alternates 1 \
	--solver Randomized \
	--probability_limits $Q

mkdir -p $ASSIGNMENTS_FOLDER
mv assignments.json $ASSIGNMENTS_FOLDER/first_matching.json

# ---------------------------------------------------------------------------------
# Second matching. Assign a third reviewer to each paper
# ---------------------------------------------------------------------------------

# Compute constraints based on the initial matching to ensure the first 2 reviewers
# assigned to a paper remain the same.
python ICML2025/scripts/extract_matching_constraints.py \
	--assignments $ASSIGNMENTS_FOLDER/first_matching.json \
	--output $DATA_FOLDER/constraints/first_matching_constraint.csv

# Compute the constraints for the second matching.
python ICML2025/scripts/join_conflicts.py \
	--file1 $DATA_FOLDER/constraints/conflict_constraints.csv \
	--file2 $DATA_FOLDER/constraints/first_matching_constraint.csv \
	--output $DATA_FOLDER/constraints/constraints_for_second_matching.csv

# Run the matching with the new constraints.
python -m matcher \
	--scores $DATA_FOLDER/aggregated_scores.csv $DATA_FOLDER/numeric_bids.csv \
	--weights 1 1 \
	--constraints $DATA_FOLDER/constraints/constraints_for_second_matching.csv \
	--min_papers_default 0 \
	--max_papers_default 6 \
	--num_reviewers 3 \
	--num_alternates 1 \
	--solver Randomized \
	--probability_limits $Q

mv assignments.json $ASSIGNMENTS_FOLDER/second_matching.json

# ---------------------------------------------------------------------------------
# Third matching. Assign a fourth reviewer to each paper
# ---------------------------------------------------------------------------------

# Compute constraints based on the second matching to ensure the first 3 reviewers
# assigned to a paper remain the same.
python ICML2025/scripts/extract_matching_constraints.py \
	--assignments $ASSIGNMENTS_FOLDER/second_matching.json \
	--output $DATA_FOLDER/constraints/second_matching_constraint.csv

# Compute geographical constraints based on the initial matching to ensure that
# reviewers
echo TODO

# Compute the constraints for the third matching.
python ICML2025/scripts/join_conflicts.py \
	--file1 $DATA_FOLDER/constraints/conflict_constraints.csv \
	--file2 $DATA_FOLDER/constraints/second_matching_constraint.csv \
	--output $DATA_FOLDER/constraints/constraints_for_third_matching.csv

# Re-run the matching with the additional constraints.
python -m matcher \
	--scores $DATA_FOLDER/aggregated_scores.csv $DATA_FOLDER/numeric_bids.csv \
	--weights 1 1 \
	--constraints $DATA_FOLDER/constraints/constraints_for_third_matching.csv \
	--min_papers_default 0 \
	--max_papers_default 6 \
	--num_reviewers 4 \
	--num_alternates 1 \
	--solver Randomized \
	--probability_limits $Q

mv assignments.json $ASSIGNMENTS_FOLDER/third_matching.json