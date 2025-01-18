# ICML 2025 OpenReview Matcher

## Setup

```
conda create -n openreview-matcher python=3.10
conda activate openreview-matcher
pip install -e .
```

## Aggregate scores

```
python ICML2025/aggregate_scores.py --quantile 0.75
```



TODO:
* [ ] Compute a quantile over the scores
* [ ] Make an initial matching
* [ ] Implement Simon's suggestion (?)