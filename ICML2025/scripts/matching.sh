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

conda create -n openreview-matcher python=3.10
conda activate openreview-matcher
pip install .

# ----------------------------------------------------------------------------------
# Hyper-parameters
# ----------------------------------------------------------------------------------

export DATA_FOLDER="ICML2025/data"
export QUANTILE=0.75
export UPWEIGHT_OR_PAPERS=True
export Q=0.5 # Upper bound on the marginal probability of each reviewer-paper pair being matched, for "Randomized" matcher

# ----------------------------------------------------------------------------------
# Pre-processing
# ----------------------------------------------------------------------------------

# Aggregate affinity scores using the 0.75 quantile
python -m affinity \
	--input ICML2025/data/scores_with_origin.csv \
	--output ICML2025/data/aggregated_scores.csv
	--quantile 0.75 \

# Filter out suspicious bids. TODO: implement and document
bash ICML2025/scripts/secure-paper-bidding.sh

# ---------------------------------------------------------------------------------
# Initial Matching of 2 reviewers per paper. The 3th reviewer is assigned later
# ---------------------------------------------------------------------------------

# This matching requires two sources of constraints, which need to be aggregated for the matcher:
# * ICML2025/data/conflict_constraints.csv: [paper_id, reviewer_id, constraint]
# * ICML2025/data/first_time_reviewer_constraints.csv: [paper_id, reviewer_id, constraint]

# For constraint files, the possible values for the constraint attribute are:
# * -1: conflict
# * 0: no effect
# * 1: forced assignment

# Aggregate constraints. TODO: implement
python ICML2025/scripts/join_conflicts.py \
	--file1 ICML2025/data/conflict_constraints.csv \
	--file2 ICML2025/data/first_time_reviewer_constraints.csv \
	--output ICML2025/data/constraints_for_first_matching.csv

# Initial matching. This expects the following files:
# * ICML2025/data/aggregated_scores.csv [paper_id, reviewer_id, score]
# * ICML2025/data/numeric_bids.csv: [paper_id, reviewer_id, numeric_bid]

python -m matcher \
	--scores ICML2025/data/aggregated_scores.csv ICML2025/data/numeric_bids.csv \
	--weights 1 1 \
	--constraints ICML2025/data/constraints_for_first_matching.csv \
	--min_papers_default 0 \
	--max_papers_default 6 \
	--num_reviewers 3 \
	--num_alternates 1 \
	--solver Randomized \
	--probability_limits 0.5

# ---------------------------------------------------------------------------------
# Second matching
# ---------------------------------------------------------------------------------

# Compute constraints based on the initial matching to ensure the first three reviewers
# assigned to a paper remain the same.
echo TODO

# Compute geographical constraints based on the initial matching to ensure that
# reviewers
echo TODO

# Re-run the matching with the additional constraints.
python -m matcher \
	--scores ICML2025/data/aggregated_scores_q_0.75.csv ICML2025/data/numeric_bids.csv \
	--weights 1 1 \
	--constraints ICML2025/data/conflict_constraints.csv ICML2025/data/geographical_constraints.csv \
	--min_papers_default 0 \
	--max_papers_default 6 \
	--num_reviewers 4 \
	--num_alternates 1 \
	--solver Randomized \
	--probability_limits 0.5