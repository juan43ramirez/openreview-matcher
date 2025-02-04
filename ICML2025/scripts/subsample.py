# Subsample bids and constraints
import pandas as pd
import argparse
import numpy as np

N = 1000

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument('--scores', type=str, required=True)
    arg_parser.add_argument('--files', type=str, nargs="+", help="List of files to subsample")

    args = arg_parser.parse_args()

    print("\nSubsampling files for debugging...")

    print("\nLoading scores...")
    scores = pd.read_csv(args.scores, header=None)
    submissions = scores[0].unique()
    reviewers = scores[1].unique()
    print(f"Loaded {len(submissions)} submissions and {len(reviewers)} reviewers.")

    print(f"\nSubsampling scores to {N} submissions and {N} reviewers...")
    # Subsample the number of papers to N for debugging purposes
    sampled_submissions = np.random.choice(submissions, N, replace=False)
    scores = scores[scores[0].isin(sampled_submissions)]

    # Subsample the number of reviewers to N for debugging purposes
    sampled_reviewers = np.random.choice(reviewers, N, replace=False)
    scores = scores[scores[1].isin(sampled_reviewers)]
    scores.to_csv(args.scores, header=False, index=False)

    print(f"Subsampled {len(scores)} scores from {N} submissions and {N} reviewers.")

    for file in args.files:
        print(f"\nSubsampling {file.split('/')[-1]}...")
        df = pd.read_csv(file, header=None)
        num_items = len(df)

        if len(df.columns) == 3:
            # Three columns: submission, reviewer, score
            df = df[df[0].isin(sampled_submissions) & df[1].isin(sampled_reviewers)]
            num_submissions, num_reviewers = df[0].nunique(), df[1].nunique()
            df.to_csv(file, header=False, index=False)
            print(f"Subsampled {len(df)}/{num_items} rows from {num_submissions} submissions and {num_reviewers} reviewers.")
        elif len(df.columns) == 2:
            # Two columns: reviewer, supply
            df = df[df[0].isin(sampled_reviewers)]
            num_reviewers = df[0].nunique()
            df.to_csv(file, header=False, index=False)
            print(f"Subsampled {len(df)}/{num_items} rows from {num_reviewers} reviewers.")
        else:
            raise ValueError(f"Invalid number of columns in {file}.")