import argparse
import pandas as pd

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--input", type=str, required=True)
    argparser.add_argument("--output", type=str, required=True)
    argparser.add_argument("--min-pos-bids", type=float, required=True)

    args = argparser.parse_args()

    print(f"\nKeeping only the positive bids from reviewers with at least {args.min_pos_bids} positive bids...")

    df = pd.read_csv(args.input, header=None, names=["paper_id", "reviewer_id", "bid"])
    num_bidding_reviewers = len(df["reviewer_id"].unique())

    print(f"Loaded {len(df)} bids from {num_bidding_reviewers} reviewers.")

    # Group by reviewer_id and count the number of positive bids. Filter out reviewers
    # with less than min-pos-bids
    pos_bids = df[df["bid"] > 0].groupby("reviewer_id").size()
    pos_bids = pos_bids[pos_bids >= args.min_pos_bids]
    num_nulled_reviewers = num_bidding_reviewers - len(pos_bids)

    # Keep only the positive bids from reviewers with at least min-pos-bids
    # Keep the negative bids from everyone (this includes the "Conflict" bids)
    filtered_bids = df[df["reviewer_id"].isin(pos_bids.index) | (df["bid"] < 0)]

    print(f"Filtered out bids from {num_nulled_reviewers} reviewers.")

    filtered_bids.to_csv(args.output, header=False, index=False)
    
    num_papers = len(filtered_bids["paper_id"].unique())
    num_reviewers = len(filtered_bids["reviewer_id"].unique())
    
    print(f"Done. Kept a total of {len(filtered_bids)}/{len(df)} bids from {num_reviewers} reviewers to {num_papers} papers.")