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

def fetch_submission_ids():
    print(f"\nFetching submission ids")
    venue_group = CLIENT_V2.get_group(CONFERENCE_ID)
    submission_name = venue_group.content['submission_name']['value']
    submissions = CLIENT_V2.get_all_notes(invitation=f'{CONFERENCE_ID}/-/{submission_name}')
    return [submission.id for submission in submissions]

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
    argparser.add_argument("--no_or_paper_reviewers", type=str, required=True)
    argparser.add_argument("--output", type=str, required=True)

    args = argparser.parse_args()

    # ---------------------------------------------------------
    # Fetch first-time reviewer information and submission IDs in parallel
    # ---------------------------------------------------------
    with ThreadPoolExecutor() as executor:
        rev_info_future = executor.submit(fetch_first_time_reviewer_info)
        submission_ids_future = executor.submit(fetch_submission_ids)

        rev_info = rev_info_future.result()
        submission_ids = submission_ids_future.result()

    # ---------------------------------------------------------
    # Extract first-time reviewer constraints and no OR paper constraints
    # ---------------------------------------------------------
    print(f"\nExtracting constraints")
    no_or_paper_reviewers = set(pd.read_csv(args.no_or_paper_reviewers, header=None)[0])

    # Collect all constraints
    rows, first_time_reviewers, no_or_paper_reviewers_set = extract_constraints(submission_ids, rev_info, no_or_paper_reviewers)

    # ---------------------------------------------------------
    # Save the constraints to CSV
    # ---------------------------------------------------------
    df = pd.DataFrame(rows, columns=["paper_id", "reviewer_id", "constraint"])
    df.to_csv(args.output, index=False, header=False)

    # ---------------------------------------------------------
    # Print counts of first-time reviewers and reviewers with no OR papers
    # ---------------------------------------------------------
    print(f"Number of first-time reviewers: {len(first_time_reviewers)}")
    print(f"Number of reviewers with no OR papers: {len(no_or_paper_reviewers)}")

    # Intersection of first-time reviewers and reviewers with no OR papers
    first_time_and_no_or = len(no_or_paper_reviewers) - len(no_or_paper_reviewers_set)
    print(f"Number of reviewers with no OR papers and who are first-time reviewers: {first_time_and_no_or}")

    print(f"Extracted {len(df)} constraints, for a total of {len(no_or_paper_reviewers_set) + len(first_time_reviewers)} unique reviewers")
