# Subsample bids and constraints
import pandas as pd
import argparse

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    
    arg_parser.add_argument('--scores', type=str, required=True)
    arg_parser.add_argument('--files', type=str, nargs="+", help="List of files to subsample")
    
    args = arg_parser.parse_args()
    
    print("\nSubsampling files...")
    
    print("\nLoading scores...")
    scores = pd.read_csv(args.scores, header=None)
    submissions = scores[0].unique()
    reviewers = scores[1].unique()
    print(f"Loaded {len(submissions)} submissions and {len(reviewers)} reviewers.")

    for file in args.files:
        print(f"\nSubsampling {file.split('/')[-1]}...")
        df = pd.read_csv(file, header=None)
        df = df[df[0].isin(submissions) & df[1].isin(reviewers)]
        num_submissions, num_reviewers = df[0].nunique(), df[1].nunique()
        df.to_csv(file, header=False, index=False)
        print(f"Subsampled {len(df)} constraints from {num_submissions} submissions and {num_reviewers} reviewers.")