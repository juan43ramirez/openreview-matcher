# Aggregate scores using the max across a reviewer's papers'
echo "\nAggregating scores using max"
python ICML2025/scripts/aggregate_scores.py --quantile 1

# Run an initial matching with all reviewers and:
# * 10 reviewers per paper
# * 6 review per reviewer
# * MAX for the aggregation of scores
echo "\nRunning initial matching with all reviewers"

python -m matcher \
	--scores ICML2025/data/aggregated_scores_q_1.0.csv ICML2025/data/numeric_bids.csv \
	--weights 1 1 \
	--min_papers_default 0 \
	--max_papers_default 6 \
	--num_reviewers 10 \
	--num_alternates 0 \
	--solver Randomized \
	--probability_limits 0.5 \
    --allow_zero_score_assignments

mkdir ICML2025/assignments
mv assignments.json ICML2025/assignments/all_reviewers_10_1.json

# Run reviewer subsampling script
echo "\nSubsampling reviewers"
python ICML2025/scripts/subsample_reviewers.py


# Run new matching with subsampled reviewers - Max aggregation
echo "\nRunning matching with subsampled reviewers - Max aggregation"
python -m matcher \
    --scores ICML2025/data/subsampled_reviewers/aggregated_scores_q_1.0.csv ICML2025/data/subsampled_reviewers/numeric_bids.csv \
    --weights 1 1 \
    --min_papers_default 0 \
    --max_papers_default 5 \
    --num_reviewers 4 \
    --num_alternates 0 \
    --solver Randomized \
    --probability_limits 0.5 \
    --allow_zero_score_assignments

mkdir ICML2025/assignments/subsampled_reviewers
mv assignments.json ICML2025/assignments/subsampled_reviewers/max_4_5.json

# Run new matching with subsampled reviewers - q 0.75 aggregation
echo "\nRunning matching with subsampled reviewers - q 0.75 aggregation"
python -m matcher \
    --scores ICML2025/data/subsampled_reviewers/aggregated_scores_q_0.75.csv ICML2025/data/subsampled_reviewers/numeric_bids.csv \
    --weights 1 1 \
    --min_papers_default 0 \
    --max_papers_default 5 \
    --num_reviewers 4 \
    --num_alternates 0 \
    --solver Randomized \
    --probability_limits 0.5 \
    --allow_zero_score_assignments


mv assignments.json ICML2025/assignments/subsampled_reviewers/q_0.75_4_5.json

