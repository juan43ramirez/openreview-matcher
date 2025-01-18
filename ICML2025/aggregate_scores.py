import os
import pandas as pd
import numpy as np
import time
import argparse

def weighted_quantile(data, weights, quantile):
    # Sort data and weights by data
    sorted_data, sorted_weights = zip(*sorted(zip(data, weights)))
    sorted_data = np.array(sorted_data)
    sorted_weights = np.array(sorted_weights)

    # Compute the cumulative sum of the weights
    cumsum_weights = np.cumsum(sorted_weights).astype(float)

    # Normalize the cumulative sum of weights
    cumsum_weights /= cumsum_weights[-1]

    # Find the index where the cumulative weight exceeds the desired quantile
    return np.interp(quantile, cumsum_weights, sorted_data)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--quantile", type=float, default=0.75)
    args = argparser.parse_args()

    QUANTILE = args.quantile

    initial_time = time.time()

    print("Reading scores file")

    csv_path = os.path.join(os.getcwd(), "ICML2025/scores_specter2_scincl.csv")
    col_names = ["paper_id", "reviewer_id", "score"]

    with open(csv_path, 'r') as file:
        data = [line.strip().split(',') for line in file]
    max_length = max(len(row) for row in data)
    normalized_data = [row + [None] * (max_length - len(row)) for row in data]
    df = pd.DataFrame(normalized_data)

    print("Scores file read in", time.time() - initial_time, "seconds")

    print("Computing weighted quantile")
    current_time = time.time()

    origin_map = {
        "OR": 1.5,
        "dblp": 1.5,
        "other": 1,
    }

    with open(csv_path, 'r') as file:
        for line in file:
            paper_id, reviewer_id, *rest = line.split(",")
            scores, origin_weights = [], []

            for val in rest:
                try:
                    float(val)
                    scores.append(val)
                except ValueError:
                    # origin_weights.append(origin_map[val])
                    origin_weights.append(1)

            # Compute score quantile
            scores = np.array(scores, dtype=float)
            weighted_quantile_value = weighted_quantile(scores, origin_weights, QUANTILE)

            df = pd.concat([df, pd.DataFrame([[paper_id, reviewer_id, weighted_quantile_value]], columns=col_names)], ignore_index=True)

    print("Scores file read in", time.time() - current_time, "seconds")

    df.to_csv("ICML2025/aggregated_scores._q_" + str(QUANTILE) + ".csv", index=False)