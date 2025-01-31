import argparse
import pandas as pd

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--input", type=str, required=True)
    argparser.add_argument("--output", type=str, required=True)
    argparser.add_argument("--min-pos-bids", type=float, required=True)

    args = argparser.parse_args()

    print(f"\nFiltering bids with at least {args.min_pos_bids} positive bids")

    df = pd.read_csv(args.input, header=None, names=["paper_id", "reviewer_id", "bid"])

    # Group by reviewer_id and count the number of positive bids. Filter out reviewers
    # with less than min-pos-bids
    pos_bids = df[df["bid"] > 0].groupby("reviewer_id").size()
    pos_bids = pos_bids[pos_bids >= args.min_pos_bids]

    # Filter out reviewers with less than min-pos-bids
    filtered_bids = df[df["reviewer_id"].isin(pos_bids.index)]

    filtered_bids.to_csv(args.output, header=False, index=False)
    
    print(f"Done. Kept a total of {len(filtered_bids)}/{len(df)} bids")