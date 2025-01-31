import argparse
import pandas as pd
import json

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--assignments", type=str, required=True)
    argparser.add_argument("--output", type=str, required=True)

    args = argparser.parse_args()

    print(f"\nExtracting matching constraints")

    # assignments is a json file with the following format:
    # {
    #     "paper_id": {
    #         "review_id",
    #         "score",
    #      },
    #  ...
    # }
    with open(args.assignments, "r") as f:
        data = json.load(f)

    # output is a CSV file with the following format:
    # paper_id, review_id, 1
    rows = []
    for paper_id, reviews in data.items():
        for review in reviews:
            rows.append((paper_id, review["user"], 1)) # 1 means a forced assignment

    df = pd.DataFrame(rows) # [paper_id, review_id, constraint]
    df.to_csv(args.output, index=False, header=False)

    print(f"Done. Extracted {len(df)} matching constraints")

