import argparse
import pandas as pd

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--emergency_reviewers_files", type=str, nargs="+", help="List of files with emergency reviewers")
    argparser.add_argument("--files", type=str, nargs="+", help="List of files to subsample")

    args = argparser.parse_args()

    print(f"\nFiltering reviewers from the emergency reviewers list")

    emergency_reviewers = set()
    for file in args.emergency_reviewers_files:
        this_reviewers = set(pd.read_csv(file, header=None)[0])
        emergency_reviewers = emergency_reviewers.union(this_reviewers)

    print(f"Loaded {len(emergency_reviewers)} emergency reviewers")

    for file in args.files:

        print(f"\nRemoving emergency reviewers from {file}")
        df = pd.read_csv(file, header=None)

        if len(df.columns) == 3:
            # If file has 3 columns:
            reviewer_column = 1
        elif len(df.columns) == 2:
            # If file has 2 columns:
            reviewer_column = 0
        else:
            raise ValueError("File should have 2 or 3 columns")

        num_reviewers_in_file = len(df[reviewer_column].unique())
        print(f"Found {num_reviewers_in_file} reviewers")

        df = df[~df[reviewer_column].isin(emergency_reviewers)]
        num_reviewer_after_filter = len(df[reviewer_column].unique())

        print(f"Removed {num_reviewers_in_file - num_reviewer_after_filter} reviewers")
        print(f"Kept {num_reviewer_after_filter} reviewers")

        df.to_csv(file, header=False, index=False)
        print(f"Saved filtered file to {file}")

    print("\nDone!")