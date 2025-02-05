import numpy as np
import argparse
import pandas as pd
import openreview
import os
import time

# Use environment variables to store the username and password
OR_USERNAME = os.environ.get('OPENREVIEW_USERNAME')
OR_PASSWORD = os.environ.get('OPENREVIEW_PASSWORD')

CONFERENCE_ID = 'ICML.cc/2024/Conference'

CLIENT_V1 = openreview.Client(
    baseurl='https://api.openreview.net',
    username=OR_USERNAME,
    password=OR_PASSWORD,
)

CLIENT_V2 = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username=OR_USERNAME,
    password=OR_PASSWORD
)

SEED = 0


def get_authors():

    # Code for getting all submissions below.
    # NOTE: I did not find a way to get notes by submission ID
    submissions_v1 = CLIENT_V1.get_all_notes(
        invitation=f'{CONFERENCE_ID}/-/Submission',
        )

    # This code gets *all* submissions, which may include withdrawn and desk-rejected papers
    venue_group = CLIENT_V2.get_group(CONFERENCE_ID)
    submission_name = venue_group.content['submission_name']['value']
    submissions_v2 = CLIENT_V2.get_all_notes(invitation=f'{CONFERENCE_ID}/-/{submission_name}')

    # # This code gets submissions under review only
    # venue_group = client_v2.get_group(CONFERENCE_ID)
    # under_review_id = venue_group.content['submission_venue_id']['value']
    # submissions = client_v2.get_all_notes(content={'venueid': under_review_id})

    all_submissions = submissions_v1 + submissions_v2
    assert len(submissions_v1) == 0
    print("no submissions from the v1 API")  # not sure why that is.
    #print("# submissions from the v2 API:", len(submissions_v2))

    author2sub_ids = {}
    sub_id2authors = {}
    sub_id2title = {}
    all_submission_ids = []
    for submission in all_submissions:
        all_submission_ids.append(submission.id)
        sub_id2authors[submission.id] = submission.content['authorids']['value']
        sub_id2title[submission.id] = submission.content['title']['value']
        for author_id in submission.content['authorids']['value']:
            if author_id not in author2sub_ids.keys():
                author2sub_ids[author_id] = []
            author2sub_ids[author_id].append(submission.id)

    return author2sub_ids, sub_id2authors, sub_id2title, np.unique(all_submission_ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run TellTail algorithm')
    parser.add_argument('--rm_bids', type=str, default='ICML2025/data/removed_bids.csv')
    #parser.add_argument('--filtered_file', type=str, default='ICML2025/data/filtered_numeric_bids.csv')

    args = parser.parse_args()
    folder = args.rm_bids.replace(os.path.basename(args.rm_bids), '')

    #rm_bids = pd.read_csv(args.rm_bids, header=None, index_col=None)

    rev2bids = {}
    with open(args.rm_bids, "r") as file:
        for line in file:
            if "Trial" not in line:
                sub_id, rev_id = line.split(",")
                if rev_id not in rev2bids.keys():
                    rev2bids[rev_id] = []
                rev2bids[rev_id].append(sub_id)

    authors2sub_ids, sub_id2authors, sub_id2title, all_submission_ids_ = get_authors()
    #print("Number of reviewers (bid file):", len(set(all_reviewer_ids)))
    #print("Number of authors (API):", len(authors2sub_ids))
    #print("Intersection of the above two:", len(set(authors2sub_ids.keys()) & set(all_reviewer_ids)))
    #print("Number of Submissions (API):", len(all_submission_ids_))
    #print("Number of Submissions (bid file):", len(all_submission_ids))
    #print("Intersection of the above two:", len(set(all_submission_ids) & set(all_submission_ids_)))

    # producing list of removed bids with extra info
    new_csv_lines = []
    with open(args.rm_bids, "r") as file:
        for line in file:
            if "Trial" in line:
                new_csv_lines.append(line)
            else:
                sub_id, rev_id = line.split(",")
                sub_authors = sub_id2authors[sub_id]
                sub_title = sub_id2title[sub_id]
                colluding_authors = []
                #for author in sub_authors:
                #    if len(set(rev2bids[rev_id]) & set(authors2sub_ids[author])) > 0:
                #        colluding_authors.append(author)
                #new_csv_lines.append(f"{sub_id},{sub_title},{sub_authors},{colluding_authors},{rev_id}")
                new_csv_lines.append(f"{sub_id},{sub_title},{sub_authors},{rev_id}")

    filename = os.path.join(folder, "removed_bids_new.csv")
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, "w", newline='') as file:
        for line in new_csv_lines:
                file.write(line)
                #file.write('\n')


"""
HOW TO USE:
- Might want to change the CONFERENCE_ID on line 12 to "2025".
- Give path to cvs file containing bids via the --bids argument.
- Code will produce two files in the folder containing the bid csv file: 
    - removed_bids.csv : List of bids that were removed at each trial.
    - filtered_bids.csv : List of original bids but without suspicious bids.
"""

