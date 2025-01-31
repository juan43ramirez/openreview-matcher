import os
import pandas as pd
import numpy as np
import time
import argparse
from tqdm import tqdm
import multiprocessing as mp

def weighted_quantile(values, weights, quantiles):
    values = np.asarray(values).astype(float)
    weights = np.asarray(weights).astype(float)
    quantiles = np.asarray(quantiles).astype(float)

    assert np.all((0 <= quantiles) & (quantiles <= 1)), 'Quantiles should be in [0, 1]'

    sorter = np.argsort(values)
    values, weights = values[sorter], weights[sorter]

    weighted_quantiles = np.cumsum(weights) - 0.5 * weights
    weighted_quantiles /= np.sum(weights)

    return np.interp(quantiles, weighted_quantiles, values)

def process_file(file_path):
    """ Reads a full CSV file, applies weights, computes weighted quantiles, and returns results. """
    scores = pd.read_csv(file_path, header=None)
    scores.loc[:, 3] = scores.loc[:, 3].map(weights_per_origin)  # Apply weights

    grouped = scores.groupby([0, 1])
    results = [process_group(group) for group in grouped]
    return results

def process_group(group_data):
    """ Processes a single (paper_id, reviewer_id) group. """
    (paper_id, reviewer_id), group = group_data
    scores, weights = group[2].values, group[3].values
    weighted_q = weighted_quantile(scores, weights, args.quantile)
    assert 0 <= weighted_q <= 1, f"Invalid affinity: {weighted_q}"
    return [paper_id, reviewer_id, weighted_q]

def save_results_in_chunks(results, output_path, chunk_size=10000):
    """ Saves results to CSV in chunks to avoid memory issues. """
    for i in range(0, len(results), chunk_size):
        chunk = results[i:i+chunk_size]
        df_chunk = pd.DataFrame(chunk, columns=[0, 1, 2])  # Ensure columns are named correctly
        df_chunk.to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--scores_folder", type=str, required=True)
    argparser.add_argument("--output", type=str, required=True)
    argparser.add_argument("--quantile", type=float, default=0.75)
    argparser.add_argument(
        "--or_weight",
        type=float,
        default=1.0,
        help="Weight for papers from OpenReview. Papers from other sources have a weight of 1."
    )

    args = argparser.parse_args()

    weights_per_origin = {"OR": args.or_weight, "dblp": 1.0, "other": 1.0}

    print(f"\nAggregating scores with quantile {args.quantile}")
    start_time = time.time()

    csv_files = [os.path.join(args.scores_folder, f) for f in os.listdir(args.scores_folder) if f.endswith(".csv")]

    num_workers = max(1, mp.cpu_count() - 1)  # Leave one core free
    print(f"Processing {len(csv_files)} files with {num_workers} workers")

    # Parallelize file reading and processing
    with mp.Pool(num_workers) as pool:
        all_results = list(tqdm(pool.imap_unordered(process_file, csv_files), total=len(csv_files), desc="Processing Files"))

    # Flatten results and create final DataFrame
    final_results = [entry for sublist in all_results for entry in sublist]

    final_df = pd.DataFrame(final_results)
    num_papers = final_df[0].nunique()
    num_reviewers = final_df[1].nunique()
    
    print(f"\nAggregated {len(final_df)} scores from {num_papers} papers and {num_reviewers} reviewers")
    
    # Check there are no duplicates per (paper_id, reviewer_id) pair
    assert final_df.duplicated(subset=[0, 1]).sum() == 0, "Duplicated entries found"

    output_path = os.path.join(os.getcwd(), args.output)
    save_results_in_chunks(final_results, output_path)

    print(f"\nProcessing completed in {(time.time() - start_time) / 60:.2f} minutes")
    print(f"Aggregated results saved to {output_path}")
