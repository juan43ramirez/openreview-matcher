import argparse
import pandas as pd
import json
import openreview
import os

# Use environment variables to store the username and password
OR_USERNAME = os.environ.get('OPENREVIEW_USERNAME')
OR_PASSWORD = os.environ.get('OPENREVIEW_PASSWORD')

CONFERENCE_ID = 'ICML.cc/2025/Conference'

CLIENT_V2 = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username=OR_USERNAME,
    password=OR_PASSWORD
    )

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--output", type=str, required=True)

    args = argparser.parse_args()

    # ---------------------------------------------------------
    # Fetch first-time reviewer information
    # ---------------------------------------------------------
    rev_regs=list(openreview.tools.iterget_notes(CLIENT_V2, invitation='ICML.cc/2025/Conference/Reviewers/-/Registration'))

    rev_info={}
    for reg in rev_regs:
        rev_info[reg.signatures[0]]={
            'first-time': reg.content['first_time_reviewer']['value'],
            'area': reg.content['primary_area']['value'],
            'level': reg.content['level_of_reviewer']['value']
        }

    print(f"\nExtracting first-time reviewer constraints")

    # This code gets *all* submissions, which may include withdrawn and desk-rejected papers
    venue_group = CLIENT_V2.get_group(CONFERENCE_ID)
    submission_name = venue_group.content['submission_name']['value']
    submissions = CLIENT_V2.get_all_notes(invitation=f'{CONFERENCE_ID}/-/{submission_name}')
    submission_ids = [submission.id for submission in submissions]

    # output is a CSV file with the following format:
    # paper_id, reviewer_id, -1
    # for every paper_id, reviewer_id pair where the reviewer is a first-time reviewer
    rows = []
    for paper_id in submission_ids:
        for reviewer_id, content in rev_info.items():
            if content["first-time"] == "Yes":
                rows.append((paper_id, reviewer_id, -1))

    num_first_time_reviewers = int(len(rows) / len(submission_ids))

    df = pd.DataFrame(rows) # [paper_id, review_id, constraint]
    df.to_csv(args.output, index=False, header=False)

    print(f"Done. Extracted {len(df)} first-time reviewer constraints, for a total of {num_first_time_reviewers} first-time reviewers")