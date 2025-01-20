import pandas as pd
import numpy as np
import os

# Gather JSON with assignments
# Load into pandas
# Subsample 80 unique reviewers at random
# Save this list
# Modify bids and scores to only include these reviewers

NUM_REVIEWERS = 82 # 82 * 5 = 410 reviews available, for 102 (papers) * 4 = 408 reviews required
SEED = 0

if __name__ == "__main__":
    # Load the data
    assignments = pd.read_json("ICML2025/assignments/all_reviewers_10_1.json")

    # Extract all reviewers matched to any submission
    matched_reviewers = []
    for i in range(len(assignments)):
        matched_reviewers += assignments.iloc[i, :].apply(lambda x: x["user"]).tolist()

    matched_reviewers = list(set(matched_reviewers)) # unique reviewers

    np.random.seed(SEED)
    sampled_reviewers = np.random.choice(matched_reviewers, NUM_REVIEWERS, replace=False)
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
    bids.to_csv("ICML2025/data/subsampled_reviewers/numeric_bids.csv", index=False)

