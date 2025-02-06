import pandas as pd
import argparse
from concurrent.futures import ThreadPoolExecutor
import numpy as np

def process_file(file):
    """Reads a CSV file."""
    return pd.read_csv(file, header=None)

def aggregate(df):
    """Efficiently perform constraint aggregation."""
    # Vectorized aggregation logic using numpy for speed
    constraints = (df.values == -1).any(axis=1)
    forced_assignment = (df.values == 1).any(axis=1)

    # If there is any constraint (-1), the final value is -1
    # If there is no constraint (no -1), and there is a forced assignment (1), the final value is 1
    # If there is no constraint (no -1), and there is no forced assignment (no 1), the final value is 0
    return np.select([constraints, forced_assignment], [-1, 1], default=0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", type=str, nargs="+", help="List of files to join")
    parser.add_argument("--output", type=str, help="Output file")

    args = parser.parse_args()

    print(f"\nJoining constraints from {len(args.files)} files...")

    # Read and merge all files using ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        dfs = list(executor.map(process_file, args.files))

    num_constraints_per_file = [len(df) for df in dfs]
    print(f"Loaded {sum(num_constraints_per_file)} constraints.")

    final_df = pd.concat(dfs, axis=0, ignore_index=True)
    final_df['final'] = aggregate(final_df)

    # Drop unnecessary columns
    final_df = final_df[[0, 1, 'final']]

    # Write the result to the output file
    final_df.to_csv(args.output, index=False, header=False)

    # Assert that there are no duplicates in the assignment. If there are it means
    # that a reviewer has been assigned to the same paper during the first and second
    # matchings

    assert len(final_df) == len(final_df.drop_duplicates(subset=[0, 1])), "There are duplicates in the assignment."


    print(f"Done. Resulting file has {len(final_df)} constraints and saved to {args.output}.")
