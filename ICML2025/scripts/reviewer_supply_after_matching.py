import argparse
import pandas as pd
import json

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--assignments", type=str, required=True)
    argparser.add_argument("--max_papers", type=int, required=True)
    argparser.add_argument("--supply_output", type=str, required=True, help="Output file with reviewer supply")
    argparser.add_argument("--exhausted_reviewers_output", type=str, required=True, help="Output file with exhausted reviewers")

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

    total_supply = counts["supply"].sum()
    print(f"\nTotal reviewer supply (ignoring non-assigned reviewers): {total_supply}, as opposed to {args.max_papers * len(counts)} in the beginning.")
    print(f"Average reviewer supply (ignoring non-assigned reviewers): {total_supply / len(counts)}, as opposed to {args.max_papers} in the beginning.")

    print(f"\nSaving reviewer supply to {args.supply_output}")
    counts.to_csv(args.supply_output, index=False, header=False)

    exhausted_reviewers = counts[counts["supply"] <= 0]
    num_exhausted_reviewers = len(exhausted_reviewers)
    print(f"\nNumber of reviewers without supply: {num_exhausted_reviewers}")
    print(f"Saving exhausted reviewers to {args.exhausted_reviewers_output}")
    exhausted_reviewers.to_csv(args.exhausted_reviewers_output, index=False, header=False)

    print("\nDone!")
