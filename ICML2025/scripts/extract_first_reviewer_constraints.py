import argparse
import pandas as pd
import json

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--papers", type=str, required=True)
    argparser.add_argument("--first_time_reviewers", type=str, required=True)
    argparser.add_argument("--output", type=str, required=True)

    args = argparser.parse_args()

    print(f"\nExtracting first-time reviewer constraints")

    # papers is a csv file whose first column is the paper_id
    papers = pd.read_csv(args.papers, header=None)
    papers = papers[0].unique().tolist()

    # first_time_reviewers is a json file with the following format:
    # {
    #     "reviewer_id": {1}, # 1 means the reviewer is a first-time reviewer
    #     "reviewer_id": {0}, # 0 means the reviewer is not a first-time reviewer
    #  ...
    # }
    with open(args.first_time_reviewers, "r") as f:
        data = json.load(f)

    # output is a CSV file with the following format:
    # paper_id, reviewer_id, -1
    # for every paper_id, reviewer_id pair where the reviewer is a first-time reviewer

    num_first_time_reviewers = sum(data.values())
    rows = []
    for paper_id in papers:
        for reviewer_id, is_first_time in data.items():
            if is_first_time:
                rows.append((paper_id, reviewer_id, -1))

    df = pd.DataFrame(rows) # [paper_id, review_id, constraint]
    df.to_csv(args.output, index=False, header=False)

    print(f"Done. Extracted {len(df)} first-time reviewer constraints, for a total of {num_first_time_reviewers} first-time reviewers")

