# Subsample bids and constraints
import pandas as pd
import argparse

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    
    arg_parser.add_argument('--scores', type=str, required=True)
    arg_parser.add_argument('--bids', type=str, required=True)
    arg_parser.add_argument('--first_time_reviewer_constraints', type=str, required=True)
    arg_parser.add_argument('--conflict_constraints', type=str, required=True)
    
    args = arg_parser.parse_args()
    
    print("\nSubsampling bids and constraints...")
    
    print("\nLoading scores...")
    scores = pd.read_csv(args.scores, header=None)
    submissions = scores[0].unique()
    reviewers = scores[1].unique()
    print(f"Loaded {len(submissions)} submissions and {len(reviewers)} reviewers.")

    # Subsample bids and constraints
    print("\nSubsampling bids...")
    bids = pd.read_csv(args.bids, header=None)
    bids = bids[bids[0].isin(submissions) & bids[1].isin(reviewers)]
    bids_num_submissions, bids_num_reviewers = bids[0].nunique(), bids[1].nunique()
    bids.to_csv(args.bids, header=False, index=False)
    print(f"Subsampled {len(bids)} bids from {bids_num_submissions} submissions and {bids_num_reviewers} reviewers.")

    print("\nSubsampling constraints...")    
    first_time_reviewer_constraints = pd.read_csv(args.first_time_reviewer_constraints, header=None)
    first_time_reviewer_constraints = first_time_reviewer_constraints[first_time_reviewer_constraints[0].isin(submissions) & first_time_reviewer_constraints[1].isin(reviewers)]
    first_time_num_submissions, first_time_num_reviewers = first_time_reviewer_constraints[0].nunique(), first_time_reviewer_constraints[1].nunique()
    first_time_reviewer_constraints.to_csv(args.first_time_reviewer_constraints, header=False, index=False)
    print(f"Subsampled {len(first_time_reviewer_constraints)} first-time reviewer constraints from {first_time_num_submissions} submissions and {first_time_num_reviewers} reviewers.")
    
    print("\nSubsampling constraints...")    
    conflict_constraints = pd.read_csv(args.conflict_constraints, header=None)
    conflict_constraints = conflict_constraints[conflict_constraints[0].isin(submissions) & conflict_constraints[1].isin(reviewers)]
    conflict_num_submissions, conflict_num_reviewers = conflict_constraints[0].nunique(), conflict_constraints[1].nunique()
    conflict_constraints.to_csv(args.conflict_constraints, header=False, index=False)
    print(f"Subsampled {len(conflict_constraints)} conflict constraints from {conflict_num_submissions} submissions and {conflict_num_reviewers} reviewers.")