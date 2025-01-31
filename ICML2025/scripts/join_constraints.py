import pandas as pd
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", type=str, nargs="+", help="List of files to join")
    parser.add_argument("--output", type=str, help="Output file")

    args = parser.parse_args()

    print(f"\nJoining constraints")

    dfs = pd.read_csv(args.files[0], header=None)
    for file in args.files[1:]:
        new_df = pd.read_csv(file, header=None)
        print(f"Joining {len(new_df)} constraints from {file}")
        dfs = dfs.merge(new_df, on=[dfs.columns[0], dfs.columns[1]], how="outer")

    # There should be no row with both a constraint and a forced assignment
    assert not ((dfs == -1) & (dfs == 1)).any().any(), "Constraint and forced assignment in the same row"

    # Constraint aggregation
    # * If there is any constraint (-1), the final value is -1
    # * If there is no constraint (no -1), and there is a forced assignment (1),
    #   the final value is 1
    # * If there is no constraint (no -1), and there is no forced assignment (no 1),
    #   the final value is 0

    def aggregate(row):
        if -1 in row:
            return -1
        elif 1 in row:
            return 1
        else:
            return 0

    dfs["final"] = dfs.apply(aggregate, axis=1)

    # Drop all columns except for paper_id, reviewer_id, and final
    dfs = dfs[[0, 1, "final"]]

    dfs.to_csv(args.output, index=False, header=False)

    print(f"Done. Resulting file has {len(dfs)} constraints")