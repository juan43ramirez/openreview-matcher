import argparse
import pandas as pd
import openreview
import os
import time

# Use environment variables to store the username and password
OR_USERNAME = os.environ.get('OPENREVIEW_USERNAME')
OR_PASSWORD = os.environ.get('OPENREVIEW_PASSWORD')

CONFERENCE_ID = 'ICML.cc/2025/Conference'

CLIENT_V2 = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username=OR_USERNAME,
    password=OR_PASSWORD
)


def get_countries_from_emails(emails, country_mapping):
    countries = []
    for email in emails:
        domain = email.split('@')[-1].split('.')[-1] # get the last part of the domain
        country = country_mapping.get(domain.upper(), 'Unknown')
        if country != 'Unknown':
            countries.append(country)

    countries = list(set(countries))
    return countries


def get_submission_emails(submissions, submission_ids):
    submission_emails = []
    for submission in submissions:
        if submission.id in submission_ids:
            author_profiles = openreview.tools.get_profiles(CLIENT_V2, submission.content['authorids']['value'])
            author_emails = [profile.content['emails'] for profile in author_profiles]
            author_emails = [email for sublist in author_emails for email in sublist]

            submission_emails.append((submission.id, author_emails))

    return submission_emails

def get_reviewer_emails(reviewer_ids):

    reviewer_profiles = openreview.tools.get_profiles(CLIENT_V2, reviewer_ids)

    reviewer_emails = []
    for profile in reviewer_profiles:
        emails = profile.content.get('emails', [])
        reviewer_emails.append((profile.id, emails))

    return reviewer_emails

if __name__ == "__main__":
    """NOTE: this code uses both OpenReview API versions (v1 and v2). This should
    Not be necessary for deployment since newer venues only use the v2 API."""

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--assignments", type=str, help="Assignments file")
    argparser.add_argument("--output", type=str, help="Output file")

    args = argparser.parse_args()

    print("\nComputing geographical diversity constraints")
    initial_time = time.time()

    assignments = pd.read_csv(args.assignments, header=None)

    # ---------------------------------------------------------------------------------
    # Get email addresses of the submission authors
    # ---------------------------------------------------------------------------------


    submission_ids = assignments[0].unique().tolist()

    print("\nGetting submission authors emails for {} submissions".format(len(submission_ids)))

    # This code gets *all* submissions, which may include withdrawn and desk-rejected papers
    venue_group = CLIENT_V2.get_group(CONFERENCE_ID)
    submission_name = venue_group.content['submission_name']['value']
    submissions = CLIENT_V2.get_all_notes(invitation=f'{CONFERENCE_ID}/-/{submission_name}')

    submission_emails = get_submission_emails(submissions, submission_ids)

    # # This code gets submissions under review only
    # venue_group = client_v2.get_group(CONFERENCE_ID)
    # under_review_id = venue_group.content['submission_venue_id']['value']
    # submissions = client_v2.get_all_notes(content={'venueid': under_review_id})

    assert len(submission_emails) == len(submission_ids), "Some submissions were not found"

    print("Done in {:.2f} seconds".format((time.time() - initial_time)))
    print("Recovered emails for {} submissions".format(len(submission_emails)))

    # ---------------------------------------------------------------------------------
    # Get email addresses of the reviewers
    # ---------------------------------------------------------------------------------

    reviewer_ids = assignments[1].unique().tolist()

    print("Getting reviewer emails for {} reviewers".format(len(reviewer_ids)))

    reviewer_emails = get_reviewer_emails(reviewer_ids)

    print("Done in {:.2f} seconds".format((time.time() - initial_time)))
    print("Recovered emails for {} reviewers".format(len(reviewer_emails)))

    # ---------------------------------------------------------------------------------
    # Translate the email addresses to geographical locations
    # ---------------------------------------------------------------------------------

    print("\nTranslating emails to geographical locations")

    # Download CSV directly
    url = "https://datahub.io/core/country-list/r/data.csv" # ISO 3166-1-alpha-2
    df = pd.read_csv(url)

    # Add some common domains not included in ISO 3166-1-alpha-2
    df = df._append({'Code': 'EDU', 'Name': 'United States'}, ignore_index=True)
    df = df._append({'Code': 'UK', 'Name': 'United Kingdom'}, ignore_index=True)
    df = df._append({'Code': 'EU', 'Name': 'European Union'}, ignore_index=True)
    df = df._append({'Code': 'GOV', 'Name': 'United States'}, ignore_index=True)

    country_mapping = dict(zip(df['Code'], df['Name']))

    submission_countries = []
    for submission_id, emails in submission_emails:
        countries = get_countries_from_emails(emails, country_mapping)
        submission_countries.append((submission_id, countries))
    submission_countries = pd.DataFrame(submission_countries, columns=['paper_id', 'submission_countries'])

    reviewer_countries = []
    for reviewer_id, emails in reviewer_emails:
        countries = get_countries_from_emails(emails, country_mapping)
        reviewer_countries.append((reviewer_id, countries))
    reviewer_countries = pd.DataFrame(reviewer_countries, columns=['reviewer_id', 'reviewer_countries'])

    print("Done in {:.2f} seconds".format((time.time() - initial_time)))

    # ---------------------------------------------------------------------------------
    # Compute the constraints
    # ---------------------------------------------------------------------------------

    print("\nAssessing geographical diversity of initial assignments")

    # Add country information to the assignments dataframe
    assignments = assignments.rename(columns={0: 'paper_id', 1: 'reviewer_id', 2: 'score'})
    assignments = assignments.merge(submission_countries, left_on='paper_id', right_on='paper_id', how='left')
    assignments = assignments.merge(reviewer_countries, left_on='reviewer_id', right_on='reviewer_id', how='left')

    if len(assignments) != 3 * len(submission_ids):
        raise AssertionError("Some assignments are missing (assuming 3 reviewers per paper)")

    # Step 1
    # Does the current assignment respect the geographical diversity constraint?
    # * -1 if all assigned reviewers show a country overlap with the union of the authors' countries
    # * 0 otherwise
    assignments['overlap'] = assignments.apply(
        lambda row: -1 if any([country in row['reviewer_countries'] for country in row['submission_countries']]) else 0,
        axis=1
    )
    assignments_diversity = assignments.groupby('paper_id')['overlap'].max() # if any reviewer is 0, result is 0
    violating_papers = assignments_diversity[assignments_diversity == -1]
    num_violations = len(violating_papers)

    print("Identified {} papers with geographical diversity constraint violation".format(num_violations))


    # Step 2
    # Compute a paper, reviewer constraint dataframe for papers with violations
    # * -1 if the reviewer is from the same country as any of the authors
    # Note that the already assigned reviewers should not be considered in this step

    print("\nComputing constraints for {} papers".format(num_violations))

    lines = []

    for _, (submission_id, this_submission_countries) in submission_countries.iterrows():

        if submission_id not in violating_papers:
            # Skip already diverse papers
            continue

        assigned_reviewers = assignments[assignments['paper_id'] == submission_id]['reviewer_id'].tolist()

        for _, (reviewer_id, this_reviewer_countries) in reviewer_countries.iterrows():
            if reviewer_id in assigned_reviewers:
                # Skip already assigned reviewers
                continue

            if any([country in this_reviewer_countries for country in this_submission_countries]):
                lines.append((submission_id, reviewer_id, -1)) # -1 means constraint

    constraints = pd.DataFrame(lines)  # ['paper_id', 'reviewer_id', 'constraint']

    elapsed_time = time.time() - initial_time
    print("Done in {:.2f} seconds".format(elapsed_time))
    print("Found {} constraints".format(len(constraints)))

    constraints.to_csv(args.output, index=False, header=False)