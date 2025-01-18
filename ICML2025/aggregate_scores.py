import os
import pandas as pd
import numpy as np
import time
import argparse
import math


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
    print("Reading scores file in chunks")

    csv_path = os.path.join(os.getcwd(), "ICML2025/scores_specter2_scincl.csv")
    col_names = ["paper_id", "reviewer_id", "score"]

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
                chunk_start_time = time.time()

                # Process the current chunk
                for row in current_chunk:
                    paper_id, reviewer_id, *scores_raw = row
                    scores = []
                    weights = []

                    for value in scores_raw:
                        try:
                            scores.append(float(value))
                            weights.append(1)  # Default weight
                        except ValueError:
                            continue

                    if scores:
                        weighted_quantile_value = weighted_quantile(scores, weights, QUANTILE)
                        aggregated_data.append([paper_id, reviewer_id, weighted_quantile_value])

                # Reset the chunk
                current_chunk = []
                chunk_counter += 1
                print(f"Processed chunk {chunk_counter}/{total_chunks} in {time.time() - chunk_start_time:.2f} seconds")

        # Process the remaining rows in the last chunk
        if current_chunk:
            chunk_start_time = time.time()
            for row in current_chunk:
                paper_id, reviewer_id, *scores_raw = row
                scores = []
                weights = []

                for value in scores_raw:
                    try:
                        scores.append(float(value))
                        weights.append(1)  # Default weight
                    except ValueError:
                        continue

                if scores:
                    weighted_quantile_value = weighted_quantile(scores, weights, QUANTILE)
                    aggregated_data.append([paper_id, reviewer_id, weighted_quantile_value])

            chunk_counter += 1
            print(f"Processed chunk {chunk_counter}/{total_chunks} in {time.time() - chunk_start_time:.2f} seconds")

    # Create a DataFrame and save it to a CSV file
    aggregated_df = pd.DataFrame(aggregated_data, columns=col_names)
    output_path = f"ICML2025/aggregated_scores_q_{QUANTILE}.csv"
    aggregated_df.to_csv(output_path, index=False)

    print(f"Processing completed in {time.time() - initial_time:.2f} seconds")
    print(f"Aggregated results saved to {output_path}")
