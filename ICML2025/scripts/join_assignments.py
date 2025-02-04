import argparse
import os
import pandas as pd
import json

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--files', nargs='+', type=str, help='List of files to join')
    parser.add_argument('--output', type=str, help='Output file')

    args = parser.parse_args()

    print(f"\nJoining assignments from the following files: {args.files}")

    dfs = []
    for file in args.files:
        with open(file) as f:
            df = pd.read_csv(f, header=None)
            dfs.append(df)

    result = pd.concat(dfs)

    # Assert that the number of reviewers per paper is the same accross papers
    num_reviewers_per_paper = result.groupby(0).size().unique()
    if not len(num_reviewers_per_paper) == 1:
        raise AssertionError(f"Number of reviewers per paper is not the same accross papers: {num_reviewers_per_paper}")

    print(f"Resulting assignment has {num_reviewers_per_paper[0]} reviewers per paper")

    # Save as csv and json
    result.to_csv(args.output, index=False)
    result.to_json(args.output.replace('.csv', '.json'), orient='values')
    

    print(f"Final assignment saved to {args.output}")