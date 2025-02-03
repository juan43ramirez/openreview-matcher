import argparse
import pandas as pd
import openreview
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

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

def extract_constraints(submission_ids, rev_info, no_or_paper_reviewers):
    rows = []
    first_time_reviewers = set()
    no_or_paper_reviewers_set = set()
    all_reviewers = set()

    # First-time reviewer constraints
    for paper_id in tqdm(submission_ids, desc="Processing first-time reviewer constraints"):
        for reviewer_id, content in rev_info.items():
            all_reviewers.add(reviewer_id)
            if content["first-time"] == "Yes":
                first_time_reviewers.add(reviewer_id)
                rows.append((paper_id, reviewer_id, -1))

    # Reviewers with no OR papers constraints (excluding first-time reviewers)
    for paper_id in tqdm(submission_ids, desc="Processing reviewers without OR papers"):
        for reviewer_id in no_or_paper_reviewers:
            if reviewer_id in all_reviewers and reviewer_id not in first_time_reviewers:
                no_or_paper_reviewers_set.add(reviewer_id)
                rows.append((paper_id, reviewer_id, -1))

    return rows, first_time_reviewers, no_or_paper_reviewers_set

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--submission_ids", type=str, required=True)
    argparser.add_argument("--no_or_paper_reviewers", type=str, required=True)
    argparser.add_argument("--output", type=str, required=True)

    args = argparser.parse_args()

    # ---------------------------------------------------------
    # Fetch first-time reviewer information and submission IDs in parallel
    # ---------------------------------------------------------
    with ThreadPoolExecutor() as executor:
        rev_info_future = executor.submit(fetch_first_time_reviewer_info)
        rev_info = rev_info_future.result()

    submission_ids = pd.read_csv(args.submission_ids, header=None)[0].tolist()

    # ---------------------------------------------------------
    # Extract first-time reviewer constraints and no OR paper constraints
    # ---------------------------------------------------------
    print(f"\nExtracting constraints")
    no_or_paper_reviewers = set(pd.read_csv(args.no_or_paper_reviewers, header=None)[0])

    # Collect all constraints
    rows, first_time_reviewers, no_or_non_first_time = extract_constraints(submission_ids, rev_info, no_or_paper_reviewers)

    # ---------------------------------------------------------
    # Save the constraints to CSV
    # ---------------------------------------------------------
    df = pd.DataFrame(rows, columns=["paper_id", "reviewer_id", "constraint"])
    df.to_csv(args.output, index=False, header=False)

    # ---------------------------------------------------------
    # Print counts of first-time reviewers and reviewers with no OR papers
    # ---------------------------------------------------------
    num_submissions = len(submission_ids)

    total_reviewers = len(rev_info)
    num_first_time = len(first_time_reviewers)
    num_no_or = len(no_or_paper_reviewers)
    num_no_or_non_first_time = len(no_or_non_first_time)
    num_constrained_reviewers = num_no_or_non_first_time + num_first_time

    num_no_or_yes_first_time = num_no_or + num_first_time - num_constrained_reviewers

    assert len(df) == num_submissions * num_constrained_reviewers, f"Expected {num_submissions * num_constrained_reviewers} constraints, got {len(df)}"
    print(f"\nDone. Extracted constraints for {len(submission_ids)} submissions and {num_constrained_reviewers} reviewers")

    print(f"\nTotal number of reviewers: {total_reviewers}")
    print(f"Number of first-time reviewers: {num_first_time}")
    print(f"Number of reviewers with no OR papers: {num_no_or}")
    print(f"Number of reviewers with no OR papers and who are first-time reviewers (intersection): {num_no_or_yes_first_time}")

    print(f"Extracted {len(df)} constraints, for a total of {num_no_or_non_first_time + num_first_time} unique reviewers")
