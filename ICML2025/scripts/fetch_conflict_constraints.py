import argparse
import pandas as pd
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
    argparser.add_argument("--output", type=str, help="Output file")

    args = argparser.parse_args()

    print(f"Fetching reviewer conflicts")

    # ---------------------------------------------------------
    # Get conflicts
    # ---------------------------------------------------------

    rev_conflicts=CLIENT_V2.get_grouped_edges(
        invitation='ICML.cc/2025/Conference/Reviewers/-/Conflict',
        groupby='tail',
        select='head'
    )

    # ---------------------------------------------------------
    # Translate conflicts to constraints
    # ---------------------------------------------------------
    print(f"Translating conflicts to constraints")

    constraints = []
    for conflict in rev_conflicts:
        reviewer = conflict['id']['tail']
        for c in conflict['values']:
            paper = c['head']
            constraints.append((paper, reviewer, -1))

    df = pd.DataFrame(constraints)
    df.to_csv(args.output, index=False, header=False)

    num_papers = len(df[0].unique())
    num_reviewers = len(df[1].unique())

    print(f"Done. Extracted {len(df)} conflict constraints for {num_papers} papers and {num_reviewers} reviewers")

