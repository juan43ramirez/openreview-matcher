# ICML 2025 OpenReview Matcher

## Matcher Setup

For the matcher:
```
conda create -n openreview-matcher python=3.10
conda activate openreview-matcher
pip install .
```

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

### Translate bids

Translate the bids to numeric values:

`bids.csv` contains the bids in string format. We translate them to numerical values, using the following mapping:
- "Very High": 1
- "High": 0.5
- "Neutral": 0
- "Low": -0.5
- "Very Low": -1

To translate the bids, run the following command:

```
python ICML2025/translate_bids.py
```

This will create a file `ICML2025/data/numeric_bids.csv`.

### Filter suspicious bids

First setup the environment:
```
pip install ortools scipy tqdm torch
cd ICML2025
git clone https://github.com/facebookresearch/secure-paper-bidding
mkdirs secure-paper-bidding/data/raw_data
cd ..
```

Place the following files in `./data`:
* `papers_dictionary.json` with the following keys for every paper: `title`, `abstract`, `authors`.
* `reviewers_dictionary.json` with the following keys for every reviewer: `name`, `papers`, where each paper has the keys: `title`, `abstract`, `authors`.
* `tensor_data.pl`: dictionary with the following keys:
  * `r_subject`: reviewer's subject area vector, m-by-#subjects
  * `p_subject`: paper's subject area vector, n-by-#subjects
  * `p_title`: paper title's bag-of-words vector, n-by-#words
  * `tpms`: Affinity scores between pairs of reviewers and papers, m-by-n
  * `label`: bids scores between pairs of reviewers and papers, m-by-n

See https://drive.google.com/drive/u/0/folders/1rOJwviKDmrErHXhfgk2M9A8CN_TCjv1U for the files used during testing.

In order to do this, first ensure that `ICML2025/data` contains the following files:
* `papers.csv`, including the paper ids
* `reviewers.csv`, including the reviewer ids

And install the OpenReview API and setup the environment variables:

```
pip install openreview-py
export OPENREVIEW_USERNAME=<username>
export OPENREVIEW_PASSWORD=<password>
```


Then run the following command:

```
bash ICML2025/secure-paper-bidding.sh
```

TODO: https://github.com/sjecmen/peer-review-collusion-detection/blob/master/telltail.py


## Matching

Place the following files in `ICML2025/data`:
* `bids.csv`, with the following columns: `paper_id`, `reviewer_id`, `bid_str`
* `scores_with_origin`, with the following columns: `paper_id`, `reviewer_id`, followed by the affinity scores for each of the reviewer's papers with respect to the submission, then followed by the origins of said reviewer's papers.

Make sure you have a Gurobi license, which is required for the matching step.

For matching, we use the following command:

```
python -m matcher \
	--scores ICML2025/data/aggregated_scores_q_0.75.csv ICML2025/data/numeric_bids.csv \
	--weights 1 1 \
	--min_papers_default 0 \
	--max_papers_default 6 \
	--num_reviewers 4 \
	--num_alternates 1 \
	--solver Randomized \
	--probability_limits 0.5
```

This is also provided in the `ICML2025/matching.sh` script.