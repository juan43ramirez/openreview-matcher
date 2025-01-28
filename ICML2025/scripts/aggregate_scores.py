import os
import pandas as pd
import numpy as np
import time
import argparse
import math
from tqdm import tqdm
import multiprocessing as mp

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


def process_group(group_data):
    (paper_id, reviewer_id), group = group_data
    scores = group[2].values
    weights = group[3].values
    weighted_quantile_value = weighted_quantile(scores, weights, args.quantile)
    assert 0 <= weighted_quantile_value <= 1, f"Invalid affinity: {weighted_quantile_value}"
    return [paper_id, reviewer_id, weighted_quantile_value]

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--input", type=str, default="ICML2025/data/scores_with_origin.csv")
    argparser.add_argument("--output", type=str, default="ICML2025/data/aggregated_scores.csv")
    argparser.add_argument("--quantile", type=float, default=0.75)
    argparser.add_argument(
        "--or_weight",
        type=float,
        default=1.0,
        help="Weight for papers from OpenReview. Papers from other sources have a weight of 1."
    )

    args = argparser.parse_args()

    print(f"\nAggregating scores with quantile {args.quantile}")
    initial_time = time.time()

    csv_path = os.path.join(os.getcwd(), args.input)
    scores = pd.read_csv(csv_path, header=None)

    weights_per_origin = {
        "OR": args.or_weight,
        "dblp": 1.0,
        "other": 1.0,
    }

    scores.loc[:, 3] = np.vectorize(weights_per_origin.get)(scores.loc[:, 3])

    grouped = pd.DataFrame(scores).groupby([0, 1])

    # Parallel processing with tqdm for progress bar
    num_workers = max(1, mp.cpu_count() - 1)  # Leave one core free
    with mp.Pool(num_workers) as pool:
        aggregated_data = list(
            tqdm(pool.imap(process_group, grouped), total=len(grouped), desc="Processing Groups")
        )

    # Create a DataFrame and save it to a CSV file
    aggregated_df = pd.DataFrame(aggregated_data)

    output_path = os.path.join(os.getcwd(), args.output)
    aggregated_df.to_csv(output_path, index=False, header=False)

    print(f"Processing completed in {time.time() - initial_time:.2f} seconds")
    print(f"Aggregated results saved to {output_path}")