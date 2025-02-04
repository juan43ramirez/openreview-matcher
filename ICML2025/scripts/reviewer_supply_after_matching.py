import argparse
import pandas as pd
import json

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--assignments", type=str, required=True)
    argparser.add_argument("--max_papers", type=int, required=True)
    argparser.add_argument("--output", type=str, required=True)

    args = argparser.parse_args()

    print(f"\nGathering reviewer supply after first matching")

    # assignments is a json file with the following format:
    # {
    #     "paper_id": {
    #         "reviewer_id",
    #         "score",
    #      },
    #  ...
    # }
    with open(args.assignments, "r") as f:
        data = json.load(f)

    # output is a CSV file with the following format:
    # reviewer_id, supply

    # Count number of reviews per reviewer
    counts = {}
    for paper_id, reviews in data.items():
        for review in reviews:
            reviewer_id = review["user"]
            counts[reviewer_id] = counts.get(reviewer_id, 0) + 1

    counts = pd.DataFrame(list(counts.items()), columns=["reviewer_id", "supply"])
    
    # Supply is max_papers - number of reviews
    counts["supply"] = args.max_papers - counts["supply"]
    counts.to_csv(args.output, index=False, header=False)

    total_supply = counts["supply"].sum()

    num_reviewers_without_supply = counts[counts["supply"] <= 0].shape[0]
    print(f"\nNumber of reviewers without supply: {num_reviewers_without_supply}")

    print(f"\nTotal reviewer supply (ignoring non-assigned reviewers): {total_supply}, as opposed to {args.max_papers * len(counts)} in the beginning.")
    print(f"Average reviewer supply (ignoring non-assigned reviewers): {total_supply / len(counts)}, as opposed to {args.max_papers} in the beginning.")

    print("\nDone!")
