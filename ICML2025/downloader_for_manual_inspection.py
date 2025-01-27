"""
Download notes for all submission for ICML 2024 conference, and notes
for all the signed up reviewers. This is useful for manual inspection of the
assignment produced by various matching algorithms.
"""
import openreview
from rich import print
import pickle
import os
import pandas as pd
from tqdm import tqdm

USERNAME = os.environ.get('OPEN_REVIEW_USERNAME')
PASSWORD = os.environ.get('OPEN_REVIEW_PASSWORD')


def download_icml24_notes(client2, outpath='data/icml24_notes.pkl'):
    """Gets all notes for ICML 2024 conference. Notes here refer to a variety
    of information for each paper, such as the paper's title, abstract, authors, etc.
    """
    client = client2
    venues = client.get_group(id='venues').members
    vname = 'ICML.cc/2024/Conference'
    icmlv = [v for v in venues if  vname in v]
    assert len(icmlv) == 1, "Incorret venue name: " + vname

    venue_id = icmlv[0]
    venue_group = client.get_group(venue_id)
    submission_id = venue_group.content['submission_id']['value']

    notes = client.get_all_notes(invitation=submission_id)
    with open(outpath, 'wb') as f:
        pickle.dump(notes, f)


def download_icml24_reviewer_notes(client1, client2, reviewer_list, outpath='data/icml24_reviewers.pkl'):
    # Group into 10 reviewers per request
    all_notes_v1, all_notes_v2 = [], []
    for i in tqdm(range(0, len(reviewer_list), 10)):
        rlist = reviewer_list[i:i+10]
        notes_v1 = list(openreview.tools.iterget_notes(client1, content={'authorids': rlist}))
        notes_v2 = list(openreview.tools.iterget_notes(client2, content={'authorids': rlist}))
        all_notes_v1 += notes_v1
        all_notes_v2 += notes_v2
    all_notes = all_notes_v1 + all_notes_v2
    with open(outpath, 'wb') as f:
        pickle.dump(all_notes, f)



if __name__ == '__main__':
    icml24_path = 'data/icml24_notes.pkl'
    icml24_reviewers_path = 'data/icml24_reviewers.pkl'

    client1 = openreview.Client(
        baseurl='https://api.openreview.net',
        username=USERNAME, password=PASSWORD,
    ) 
    client2 = openreview.api.OpenReviewClient(
        baseurl='https://api2.openreview.net',
        username=USERNAME, password=PASSWORD,
    )

    # Get all the submission information for ICML 2024
    print("Downloading ICML24 notes")
    download_icml24_notes(client2, icml24_path)
    
    
    # Get the list of reviewers and their notes
    df = pd.read_csv('data/reviewers.csv')
    print(df.head())
    print(df.sample(5))
    reviewer_ids = df['user id'].tolist()
        
    print("Downloading ICML24 reviewer notes")
    download_icml24_reviewer_notes(client1, client2, reviewer_ids, icml24_reviewers_path)




# # some venues were based on OpenReview's api v1, recent venues are based on api v2
# pub_type={'OR':[],'dblp':[],'other':[]}

# for n in notes_v1:
#     if n.invitation=='dblp.org/-/record': # papers imported from DBLP
#     	pub_type['dblp'].append(n)
#     elif n.invitation=='OpenReview.net/Archive/-/Direct_Upload': # papers uploaded by user
#     	pub_type['other'].append(n)
#     else: # papers at an OpenReview venue
#     	pub_type['OR'].append(n)

# for n in notes_v2:
#     if 'DBLP.org/-/Record' in n.invitations:
#     	pub_type['dblp'].append(n)
#     elif 'OpenReview.net/Archive/-/Direct_Upload' in n.invitations:
#     	pub_type['other'].append(n)
#     else:
#     	pub_type['OR'].append(n)

# def get_submission_info(paper_id, paper_notes_dict):
#     note = paper_notes_dict[paper_id]
#     paper_info = {
#         'paper_id': note.id,
#         'paper_title': note.content['title'],
#         'paper_authors': note.content['authors'],
#         'paper_abstract': note.content['abstract']
#     }
#     return paper_info

