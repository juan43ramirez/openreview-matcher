# ICML 2025 OpenReview Matcher

## Setup

```
conda create -n openreview-matcher python=3.10
conda activate openreview-matcher
pip install .
```

Expects the following files inside the `ICML2025/data` directory:
* `bids100.csv`, with the following columns: `paper_id`, `reviewer_id`, `bid_str`
* `scores_with_origin`, with the following columns: `paper_id`, `reviewer_id`, followed by the affinity scores for each of the reviewer's papers with respect to the submission, then followed by the origins of said reviewer's papers.

Make sure you have a Gurobi license, which is required for the matching step.

## Aggregate affinity scores

To aggregate the affinity scores for each reviewer, we compute a weighted quantile of the scores, where weights are given by the origin of each paper:
- OpenReview: 1.5
- dblp: 1.5
- Other (uploaded by the reviewer): 1

To compute this aggregation, run the following command:

```
python ICML2025/aggregate_scores.py --quantile 0.75
```

This will create a file `ICML2025/data/aggregated_scores_q_0.75.csv` with the following columns: `paper_id`, `reviewer_id`, `score`.

## Suspicious bid filtering

TODO: Implement this

```
...
```

## Translate bids

`bids100.csv` contains the bids in string format. We translate them to numerical values, using the following mapping:
- "Very High": 1
- "High": 0.5
- "Neutral": 0
- "Low": -0.5
- "Very Low": -1

To translate the bids, run the following command:

```
python ICML2025/translate_bids.py
```

This will create a file `ICML2025/data/numeric_bids100.csv`.

## Matching

For matching, we use the following command:

```
python -m matcher \
	--scores ICML2025/data/aggregated_scores_q_0.75.csv ICML2025/data/numeric_bids100.csv \
	--weights 1 1 \
	--min_papers_default 0 \
	--max_papers_default 6 \
	--num_reviewers 4 \
	--num_alternates 1 \
	--solver Randomized \
	--probability_limits 0.5
```

This is also provided in the `ICML2025/matching.sh` script.