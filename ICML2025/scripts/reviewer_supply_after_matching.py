import argparse
import pandas as pd
import json

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--assignments", type=str, required=True)
    argparser.add_argument("--max_papers", type=int, required=True)
    argparser.add_argument("--supply_output", type=str, required=True, help="Output file with reviewer supply")
    argparser.add_argument("--exhausted_reviewers_output", type=str, required=True, help="Output file with exhausted reviewers")
    argparser.add_argument("--remaining_reviewer_constraints_output", type=str, required=True, help="Output file with remaining reviewer constraints")

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
    constraints = []
    for paper_id, reviews in data.items():
        for review in reviews:
            reviewer_id = review["user"]
            counts[reviewer_id] = counts.get(reviewer_id, 0) + 1
            constraints.append((paper_id, reviewer_id, -1)) # -1 is a conflict

    counts = pd.DataFrame(list(counts.items()), columns=["reviewer_id", "supply"])

    # -------------------------------------------------------
    # Save the remainder supply for each reviewer
    # -------------------------------------------------------

    # Supply is max_papers - number of reviews
    counts["supply"] = args.max_papers - counts["supply"]

    total_supply = counts["supply"].sum()
    print(f"\nTotal reviewer supply (ignoring non-assigned reviewers): {total_supply}, as opposed to {args.max_papers * len(counts)} in the beginning.")
    print(f"Average reviewer supply (ignoring non-assigned reviewers): {total_supply / len(counts)}, as opposed to {args.max_papers} in the beginning.")

    print(f"\nSaving reviewer supply to {args.supply_output}")
    counts.to_csv(args.supply_output, index=False, header=False)

    # -------------------------------------------------------
    # Save list of reviewers without supply; these will be excluded from the next matching
    # -------------------------------------------------------
    exhausted_reviewers = counts[counts["supply"] <= 0]

    num_exhausted_reviewers = len(exhausted_reviewers)
    print(f"\nNumber of reviewers without supply: {num_exhausted_reviewers}")
    print(f"Saving exhausted reviewers to {args.exhausted_reviewers_output}")

    exhausted_reviewers.to_csv(args.exhausted_reviewers_output, index=False, header=False)

    # -------------------------------------------------------
    # For each existing assignment of a reviewer with supply, set a constraint to ensure
    # that the reviewer can not be assigned to papers that they have already review
    # -------------------------------------------------------
    print(f"\nCreating constraints for reviewers with supply so they are not assigned to papers they have already reviewed")

    constraints_df = pd.DataFrame(constraints)

    # Filter out reviewers without supply
    constraints_df = constraints_df[~constraints_df[1].isin(exhausted_reviewers["reviewer_id"])]

    print(f"Saving remaining reviewer constraints to {args.remaining_reviewer_constraints_output}")

    constraints_df.to_csv(args.remaining_reviewer_constraints_output, index=False, header=False)


    print("\nDone!")
