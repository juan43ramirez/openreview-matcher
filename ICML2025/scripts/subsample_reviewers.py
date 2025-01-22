import pandas as pd
import numpy as np
import os
from collections import Counter

NUM_REVIEWERS = 81 # 81 * 5 = 405 reviews available, for 101 (papers) * 4 = 404 reviews required
SEED = 0

if __name__ == "__main__":
    # Load the data
    assignments = pd.read_json("ICML2025/assignments/all_reviewers_10_1.json")

    # Extract all reviewers matched to any submission
    matched_reviewers = []
    for i in range(len(assignments)):
        matched_reviewers += assignments.iloc[i, :].apply(lambda x: x["user"]).tolist()

    matched_reviewers = list(set(matched_reviewers)) # unique reviewers

    # Sample NUM_REVIEWERS reviewers, giving preference to reviewers who have been
    # matched to multiple submissions
    np.random.seed(SEED)

    counts = Counter(matched_reviewers)
    elements, weights = zip(*counts.items())
    sampled_reviewers = np.random.choice(elements, size=NUM_REVIEWERS, replace=False, p=np.array(weights) / sum(weights))

    assert len(sampled_reviewers) == NUM_REVIEWERS

    os.makedirs("ICML2025/data/subsampled_reviewers", exist_ok=True)

    sampled_reviewers_df = pd.DataFrame(sampled_reviewers)
    sampled_reviewers_df.to_csv("ICML2025/data/subsampled_reviewers/reviewers.csv", index=False, header=False)

    # Filter scores and bids
    scores = pd.read_csv("ICML2025/data/aggregated_scores_q_1.0.csv", header=None)
    scores = scores[scores[1].isin(sampled_reviewers)]
    scores.to_csv("ICML2025/data/subsampled_reviewers/aggregated_scores_q_1.0.csv", index=False, header=False)

    scores = pd.read_csv("ICML2025/data/aggregated_scores_q_0.75.csv", header=None)
    scores = scores[scores[1].isin(sampled_reviewers)]
    scores.to_csv("ICML2025/data/subsampled_reviewers/aggregated_scores_q_0.75.csv", index=False, header=False)

    bids = pd.read_csv("ICML2025/data/numeric_bids.csv", header=None)
    bids = bids[bids[1].isin(sampled_reviewers)]
    bids.to_csv("ICML2025/data/subsampled_reviewers/numeric_bids.csv", index=False, header=False)

