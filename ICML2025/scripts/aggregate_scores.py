import os
import pandas as pd
import numpy as np
import time
import argparse
import math

WEIGHTS_PER_ORIGIN = {
    "OR": 1.5,
    "dblp": 1.0,
    "other": 1.0,
}

def weighted_quantile(values, weights, quantiles):
    values = np.array(values).astype(float)
    quantiles = np.array(quantiles).astype(float)
    weights = np.array(weights).astype(float)

    assert np.all(quantiles >= 0) and np.all(quantiles <= 1), \
        'quantiles should be in [0, 1]'

    sorter = np.argsort(values)
    values = values[sorter]
    weights = weights[sorter]

    weighted_quantiles = np.cumsum(weights) - 0.5 * weights
    weighted_quantiles /= np.sum(weights)

    return np.interp(quantiles, weighted_quantiles, values)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--quantile", type=float, default=0.75)
    args = argparser.parse_args()

    QUANTILE = args.quantile

    initial_time = time.time()

    csv_path = os.path.join(os.getcwd(), "ICML2025/data/scores_with_origin.csv")
    scores = pd.read_csv(csv_path, header=None)
    scores.loc[:, 3] = np.vectorize(WEIGHTS_PER_ORIGIN.get)(scores.loc[:, 3])

    aggregated_data = []
    grouped = pd.DataFrame(scores).groupby([0, 1])

    for (paper_id, reviewer_id), group in grouped:
        scores = group[2].values
        weights = group[3].values
        weighted_quantile_value = weighted_quantile(scores, weights, QUANTILE)
        assert 0 <= weighted_quantile_value <= 1, f"Invalid affinity: {weighted_quantile_value}"
        aggregated_data.append([paper_id, reviewer_id, weighted_quantile_value])

    # Create a DataFrame and save it to a CSV file
    aggregated_df = pd.DataFrame(aggregated_data)

    output_path = f"ICML2025/data/aggregated_scores_q_{QUANTILE}.csv"
    aggregated_df.to_csv(output_path, index=False, header=False)

    print(f"Processing completed in {time.time() - initial_time:.2f} seconds")
    print(f"Aggregated results saved to {output_path}")
