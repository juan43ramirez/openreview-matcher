python -m matcher \
	--scores ICML2025/data/aggregated_scores_q_0.75.csv ICML2025/data/numeric_bids100.csv \
	--weights 1 1 \
	--min_papers_default 0 \
	--max_papers_default 6 \
	--num_reviewers 4 \
	--num_alternates 1 \
	--solver Randomized \
	--probability_limits 0.5
