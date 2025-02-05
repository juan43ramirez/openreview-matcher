import argparse
import pandas as pd
import openreview
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Use environment variables to store the username and password
OR_USERNAME = os.environ.get('OPENREVIEW_USERNAME')
OR_PASSWORD = os.environ.get('OPENREVIEW_PASSWORD')

CONFERENCE_ID = 'ICML.cc/2025/Conference'

CLIENT_V2 = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username=OR_USERNAME,
    password=OR_PASSWORD
)

def fetch_first_time_reviewer_info():
    print(f"\nFetching first-time reviewer information")
    rev_regs = list(openreview.tools.iterget_notes(CLIENT_V2, invitation='ICML.cc/2025/Conference/Reviewers/-/Registration'))

    rev_info = {}
    for reg in rev_regs:
        rev_info[reg.signatures[0]] = {
            'first-time': reg.content['first_time_reviewer']['value'],
            'area': reg.content['primary_area']['value'],
            'level': reg.content['level_of_reviewer']['value']
        }
    return rev_info

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()

    argparser.add_argument("--no_or_paper_reviewers", type=str, required=True)
    argparser.add_argument("--scores", type=str, required=True)
    argparser.add_argument("--bids", type=str, required=True)
    argparser.add_argument("--constraints", type=str, required=True)
    argparser.add_argument("--output_prefix", type=str, required=True)

    args = argparser.parse_args()

    # ---------------------------------------------------------
    # Fetch first-time reviewer information
    # ---------------------------------------------------------
    with ThreadPoolExecutor() as executor:
        rev_info_future = executor.submit(fetch_first_time_reviewer_info)
        rev_info = rev_info_future.result()

    # ---------------------------------------------------------
    # Extract first-time reviewer constraints and no OR paper constraints
    # ---------------------------------------------------------
    print(f"\nGathering first-time reviewer list")

    first_time_reviewers = set()
    no_or_paper_reviewers = set(pd.read_csv(args.no_or_paper_reviewers, header=None)[0])

    # First-time reviewer constraints
    for reviewer_id, content in rev_info.items():
        if content["first-time"] == "Yes":
            first_time_reviewers.add(reviewer_id)

    # We consider reviewers with no OR papers as first-time reviewers
    all_first_time_reviewers = first_time_reviewers.union(no_or_paper_reviewers)
    intersection = first_time_reviewers.intersection(no_or_paper_reviewers)

    # ---------------------------------------------------------
    # Print counts of first-time reviewers and reviewers with no OR papers
    # ---------------------------------------------------------
    num_first_time_reviewers = len(first_time_reviewers)
    num_no_or_paper_reviewers = len(no_or_paper_reviewers)
    num_intersection = len(intersection)
    num_removed_reviewers = len(all_first_time_reviewers)

    assert num_removed_reviewers == num_first_time_reviewers + num_no_or_paper_reviewers - num_intersection

    print(f"Number of first-time reviewers: {num_first_time_reviewers}")
    print(f"Number of reviewers with no OR papers: {num_no_or_paper_reviewers}")
    print(f"Number of reviewers with either no OR papers or first-time reviewers (union): {num_removed_reviewers}")
    print(f"Number of reviewers with no OR papers and who are first-time reviewers (intersection): {num_intersection}")

    # ---------------------------------------------------------
    # Save the constraints to CSV
    # ---------------------------------------------------------
    print(f"\nSaving first-time reviewer list to {args.output_prefix}_first_time_reviewers.csv")

    all_first_time_reviewers = pd.DataFrame(list(all_first_time_reviewers))
    # Filename: add prefix to the filename, not the parent directory
    filename = Path(args.no_or_paper_reviewers).parent / "first_time_reviewers.csv"
    all_first_time_reviewers.to_csv(filename, header=False, index=False)
    all_first_time_reviewers = all_first_time_reviewers[0].values

    scores = pd.read_csv(args.scores, header=None)
    bids = pd.read_csv(args.bids, header=None)
    constraints = pd.read_csv(args.constraints, header=None)

    num_reviewers_with_scores = len(scores[1].unique())
    num_reviewers_with_bids = len(bids[1].unique())
    num_reviewers_with_constraints = len(constraints[1].unique())
    total_num_reviewers = max(num_reviewers_with_scores, num_reviewers_with_bids, num_reviewers_with_constraints)

    scores = scores[~scores[1].isin(all_first_time_reviewers)]
    print(f"\nSaving scores for {len(scores[1].unique())} reviewers, out of {num_reviewers_with_scores} reviewers")
    filename = Path(args.scores).parent / f"{args.output_prefix}_scores.csv"
    scores.to_csv(filename, header=False, index=False)
    print(f"Saved filtered scores to {filename}")

    bids = bids[~bids[1].isin(all_first_time_reviewers)]
    print(f"\nSaving bids for {len(bids[1].unique())} reviewers, out of {num_reviewers_with_bids} reviewers")
    filename = Path(args.bids).parent / f"{args.output_prefix}_bids.csv"
    bids.to_csv(filename, header=False, index=False)
    print(f"Saved filtered bids to {filename}")

    constraints = constraints[~constraints[1].isin(all_first_time_reviewers)]
    print(f"\nSaving constraints for {len(constraints[1].unique())} reviewers, out of {num_reviewers_with_constraints} reviewers")
    filename = Path(args.constraints).parent / f"{args.output_prefix}_constraints.csv"
    constraints.to_csv(filename, header=False, index=False)
    print(f"Saved filtered constraints to {filename}")

    print(f"\nDone!")