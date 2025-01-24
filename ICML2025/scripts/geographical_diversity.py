import argparse
import pandas as pd
import openreview
import os
import time

# Use environment variables to store the username and password
OR_USERNAME = os.environ.get('OPENREVIEW_USERNAME')
OR_PASSWORD = os.environ.get('OPENREVIEW_PASSWORD')

CONFERENCE_ID = 'ICML.cc/2024/Conference'

def get_countries_from_emails(emails, country_mapping):
    countries = []
    for email in emails:
        domain = email.split('@')[-1].split('.')[-1] # get the last part of the domain

        if domain == "edu":
            # Assuming that all .edu domains are from the United States.
            # Note that .edu.co domains are not necessarily from the US
            country = "United States"
        else:
            country = country_mapping.get(domain.upper(), 'Unknown')

        if country != 'Unknown':
            countries.append(country)

    countries = list(set(countries))
    return countries

if __name__ == "__main__":
    """NOTE: this code uses both OpenReview API versions (v1 and v2). This should
    Not be necessary for deployment since newer venues only use the v2 API."""

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--output", type=str, help="Output file")
    argparser.add_argument("--assignments", type=str, help="Assignments file")

    args = argparser.parse_args()

    print("\nComputing geographical diversity constraints")
    initial_time = time.time()

    assignments = pd.read_csv(args.assignments, header=None)

    # Connect to OpenReview
    client_v1 = openreview.Client(
        baseurl='https://api.openreview.net',
        username=OR_USERNAME,
        password=OR_PASSWORD,
    )

    client_v2 = openreview.api.OpenReviewClient(
        baseurl='https://api2.openreview.net',
        username=OR_USERNAME,
        password=OR_PASSWORD
    )

    # ---------------------------------------------------------------------------------
    # Get email addresses of the submission authors
    # ---------------------------------------------------------------------------------


    submission_ids = assignments[0].unique().tolist()

    print("\nGetting submission authors emails for {} submissions".format(len(submission_ids)))

    # Code for getting all submissions below.
    # NOTE: I did not find a way to get notes by submission ID
    submissions_v1 = client_v1.get_all_notes(
        invitation=f'{CONFERENCE_ID}/-/Submission',
        )

    # This code gets *all* submissions, which may include withdrawn and desk-rejected papers
    venue_group = client_v2.get_group(CONFERENCE_ID)
    submission_name = venue_group.content['submission_name']['value']
    submissions_v2 = client_v2.get_all_notes(invitation=f'{CONFERENCE_ID}/-/{submission_name}')

    # # This code gets submissions under review only
    # venue_group = client_v2.get_group(CONFERENCE_ID)
    # under_review_id = venue_group.content['submission_venue_id']['value']
    # submissions = client_v2.get_all_notes(content={'venueid': under_review_id})

    all_submissions = submissions_v1 + submissions_v2

    submission_emails = []
    for submission in all_submissions:
        if submission.id in submission_ids:
            author_profiles = openreview.tools.get_profiles(client_v2, submission.content['authorids']['value'])
            author_emails = [profile.content['emails'] for profile in author_profiles]
            author_emails = [email for sublist in author_emails for email in sublist]

            submission_emails.append((submission.id, author_emails))

    # # The assert below fails since I do not have access to rejected submissions for ICML 2024
    # assert len(submission_emails) == len(submission_ids), "Some submissions were not found"

    print("Done in {:.2f} seconds".format((time.time() - initial_time)))
    print("Recovered emails for {} submissions".format(len(submission_emails)))

    # ---------------------------------------------------------------------------------
    # Get email addresses of the reviewers
    # ---------------------------------------------------------------------------------

    reviewer_ids = assignments[1].unique().tolist()

    print("Getting reviewer emails for {} reviewers".format(len(reviewer_ids)))

    reviewer_profiles_v1 = openreview.tools.get_profiles(client_v1, reviewer_ids)
    reviewer_profiles_v2 = openreview.tools.get_profiles(client_v2, reviewer_ids)

    reviewer_emails = []
    for profile_v1, profile_v2 in zip(reviewer_profiles_v1, reviewer_profiles_v2):
        emails_v1 = profile_v1.content.get('emails', [])
        emails_v2 = profile_v2.content.get('emails', [])

        assert emails_v1 == emails_v2, f"Emails for user {profile_v1.id} do not match across OpenReview API versions"

        reviewer_emails.append((profile_v1.id, emails_v1))

    print("Done in {:.2f} seconds".format((time.time() - initial_time)))
    print("Recovered emails for {} reviewers".format(len(reviewer_emails)))

    # ---------------------------------------------------------------------------------
    # Translate the email addresses to geographical locations
    # ---------------------------------------------------------------------------------

    print("\nTranslating emails to geographical locations")


    # Download CSV directly
    url = "https://datahub.io/core/country-list/r/data.csv"
    df = pd.read_csv(url)
    country_mapping = dict(zip(df['Code'], df['Name']))

    submission_countries = []
    for submission_id, emails in submission_emails:
        countries = get_countries_from_emails(emails, country_mapping)
        submission_countries.append((submission_id, countries))

    reviewer_countries = []
    for reviewer_id, emails in reviewer_emails:
        countries = get_countries_from_emails(emails, country_mapping)
        reviewer_countries.append((reviewer_id, countries))

    # Compute a paper, reviewer constraint dataframe
    # * -1 if the reviewer is from the same country as any of the authors
    # * 0 otherwise

    print("Computing constraints")

    lines = []

    for submission_id, this_submission_countries in submission_countries:
        for reviewer_id, this_reviewer_countries in reviewer_countries:
            if any([country in this_reviewer_countries for country in this_submission_countries]):
                constraint = -1
            else:
                constraint = 0

            lines.append((submission_id, reviewer_id, constraint))

    df = pd.DataFrame(lines) # ['paper_id', 'reviewer_id', 'constraint']

    assert len(df) == len(submission_countries) * len(reviewer_countries), "Some constraints are missing"

    print("Done in {:.2f} seconds".format((time.time() - initial_time)))


    df.to_csv(args.output, index=False, header=False)