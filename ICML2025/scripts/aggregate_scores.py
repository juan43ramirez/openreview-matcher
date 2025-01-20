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


def process_chunk(chunk):
    processed_data = []

    for row in chunk:
        paper_id, reviewer_id, *scores_raw = row
        scores = []
        weights = []

        for value in scores_raw:
            try:
                scores.append(float(value))
            except ValueError:
                try:
                    weights.append(WEIGHTS_PER_ORIGIN.get(value, 1.0))
                except KeyError:
                    # Exhausted the row
                    break

        if scores:
            weighted_quantile_value = weighted_quantile(scores, weights, QUANTILE)
            assert 0 <= weighted_quantile_value <= 1, f"Invalid affinity: {weighted_quantile_value}"
            processed_data.append([paper_id, reviewer_id, weighted_quantile_value])

    return processed_data


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--quantile", type=float, default=0.75)
    args = argparser.parse_args()

    QUANTILE = args.quantile

    initial_time = time.time()
    print("Reading scores file in chunks")

    csv_path = os.path.join(os.getcwd(), "ICML2025/data/scores_with_origin.csv")

    chunk_size = 10000  # Process 10,000 rows at a time

    # Estimate the number of chunks
    with open(csv_path, 'r') as file:
        total_lines = sum(1 for _ in file)
    total_chunks = math.ceil(total_lines / chunk_size)

    print(f"Total lines: {total_lines}")
    print(f"Estimated total chunks: {total_chunks}")

    aggregated_data = []
    current_chunk = []
    chunk_counter = 0

    with open(csv_path, 'r') as file:
        for i, line in enumerate(file):
            current_chunk.append(line.strip().split(','))  # Split and append the current row

            # Process the chunk when it reaches the specified size
            if len(current_chunk) == chunk_size:

                processed_data = process_chunk(current_chunk)
                aggregated_data.extend(processed_data)

                current_chunk = []
                chunk_counter += 1
                print(f"Processed chunk {chunk_counter}/{total_chunks} in {time.time() - initial_time:.2f} seconds")

        # Process the remaining rows in the last chunk
        if current_chunk:

            processed_data = process_chunk(current_chunk)

            chunk_counter += 1
            print(f"Processed chunk {chunk_counter}/{total_chunks} in {time.time() - initial_time:.2f} seconds")

    # Create a DataFrame and save it to a CSV file
    aggregated_df = pd.DataFrame(aggregated_data)
    output_path = f"ICML2025/data/aggregated_scores_q_{QUANTILE}.csv"
    aggregated_df.to_csv(output_path, index=False, header=False)

    print(f"Processing completed in {time.time() - initial_time:.2f} seconds")
    print(f"Aggregated results saved to {output_path}")
