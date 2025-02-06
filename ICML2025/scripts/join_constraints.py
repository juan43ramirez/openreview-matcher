import pandas as pd
import argparse
from concurrent.futures import ThreadPoolExecutor
import numpy as np

def process_file(file):
    """Reads a CSV file."""
    return pd.read_csv(file, header=None)

def aggregate(df):
    # If there is any constraint (-1), the final value is -1
    # If there is no constraint (no -1), and there is a forced assignment (1), the final value is 1
    # If there is no constraint (no -1), and there is no forced assignment (no 1), the final value is 0
    def aggregate_group(g):
        constraints = (g.values == -1).any()
        forced_assignment = (g.values == 1).any()
        return np.select([constraints, forced_assignment], [-1, 1], default=0)

    grouped = df.groupby([0, 1]).apply(aggregate_group).reset_index(name='final')
    return grouped

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
    print(f"Loaded {num_constraints_per_file} constraints for each file.")

    final_df = pd.concat(dfs, axis=0, ignore_index=True)
    final_df = aggregate(final_df)

    # Drop unnecessary columns
    final_df = final_df[[0, 1, 'final']]

    # Assert that there are no conflicts and forced assignments at the same time
    assert not ((final_df['final'] == -1) & (final_df['final'] == 1)).any()
    
    # Assert that there are no duplicate constraints, these should have been aggregated
    assert not final_df.duplicated(subset=[0, 1]).any()

    # Write the result to the output file
    final_df.to_csv(args.output, index=False, header=False)

    num_conflicts = (final_df['final'] == -1).sum()
    num_forced_assignments = (final_df['final'] == 1).sum()

    print(f"Aggregated constraints are {len(final_df)}, out of {sum(num_constraints_per_file)} separate constraints.")
    print(f"Number of conflicts: {num_conflicts}, number of forced assignments: {num_forced_assignments}.")
    print(f"\nDone. Constraints saved to {args.output}.")
