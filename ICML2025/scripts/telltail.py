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

'''
TellTail code is adapted from (Hooi et al., 2020)
'''

def get_local_search_init(BA_mod):
    # Return a heuristic reviewer to start at based on triangle-counting heuristic
    S_starts = []
    G = BA_mod # BA
    degs = G.sum(axis=0) + G.sum(axis=1)
    triangles = np.diag(G @ G @ G)
    heuristic = np.divide(triangles, degs, out=np.zeros(degs.shape), where=(degs > 0)).argmax()
    return heuristic

def generate_telltail_start_list(G, start_v, rng_init):
    neighbors = (G[:, start_v] + G[start_v, :])
    neighbors[start_v] += 1
    S_starts = [neighbors > 0] + [rng_init.random(G.shape[0]) > rng_init.random(1) for _ in range(10)]
    return S_starts

def run_telltail(G, start_v, rng_init):
    if np.any(G != G.T):
        G_undir = np.clip(G * G.T, 0, 1) # intersection
        graph_type = 'intersection'
    else:
        G_undir = G
        graph_type = 'none'

    S_starts = generate_telltail_start_list(G, start_v, rng_init)
    trial_results = []
    for S_start in S_starts:
        result = detect_telltail(G_undir, S_start)
        trial_results.append(result)
    x_star, f_star = max(trial_results, key=lambda elt : elt[1])
    S_detect = list(np.nonzero(x_star)[0])
    method_param_string = f'proj_type_{graph_type}'
    return S_detect, method_param_string

def modularity_matrix(A):
    d = np.sum(A, axis=0)
    m = np.sum(d) / 2
    M = A - np.outer(d, d) / (2 * m)
    return M

def detect_telltail(A, S_start):
    n = A.shape[0]
    M = modularity_matrix(A)

    x = S_start #rng.random(n) > rng.random(1)
    deg = np.sum(M[x, :], axis=0).reshape(-1, 1)
    score = metric_tail3(A, x)

    while True:
        deg_add = deg.copy()
        deg_add[x] = np.nan
        deg_del = deg.copy()
        deg_del[~x] = np.nan

        try:
            idx_add = np.nanargmax(deg_add)
        except ValueError:
            idx_add = None
        try:
            idx_del = np.nanargmin(deg_del)
        except ValueError:
            idx_del = None

        #print(f'deg_add={np.nanmax(deg_add):.1f}, deg_del={np.nanmin(deg_del):.1f}')

        x_add = x.copy()
        if idx_add is not None:
            x_add[idx_add] = 1
        x_del = x.copy()
        if idx_del is not None:
            x_del[idx_del] = 0

        score_add = metric_tail3(A, x_add)
        score_del = metric_tail3(A, x_del)

        if np.sum(x) == 0:
            assert idx_del is None
            score_del = -np.inf
        if np.sum(x) == n:
            assert idx_add is None
            score_add = -np.inf

        #print(f'size={np.sum(x)}, edges={(np.dot(x.T, np.dot(A, x)) / 2)[0, 0]:.0f}, score={score:.3f}, score_add={score_add:.3f}, score_del={score_del:.3f}', end=' ')

        if score >= score_add and score >= score_del:
            #print('-> local opt')
            break
        elif score_add >= score_del:
            #print('-> add')
            deg = deg + M[:, idx_add].reshape(-1, 1)
            x = x_add
            score = score_add
        else:
            #print('-> del')
            deg = deg - M[:, idx_del].reshape(-1, 1)
            x = x_del
            score = score_del

    return x, score

def metric_tail3(A, x):
    n = A.shape[0]
    k = np.sum(x)

    if k == 0 or k == n:
        score = 0
    else:
        s = np.floor(n / 2).astype(int)
        deg = np.sum(A, axis=0)
        m = np.sum(deg) / 2

        sumB = np.sum(deg**2) / (4 * m)
        sumB2 = m + (np.sum(deg**2)**2 - np.sum(deg**4)) / (8 * m**2) - np.dot(deg, np.dot(A, deg)) / (2 * m)
        sumBrow2 = np.sum((deg**2 / (2 * m))**2)

        p2 = s * (s - 1) / (n * (n - 1))
        p3 = s * (s - 1) * (s - 2) / (n * (n - 1) * (n - 2))
        p4 = s * (s - 1) * (s - 2) * (s - 3) / (n * (n - 1) * (n - 2) * (n - 3))

        Ymean = p2 * sumB
        wedgesum = (sumBrow2 - 2 * sumB2)
        Ymeansq = p2 * sumB2 + p3 * wedgesum + p4 * (sumB**2 - sumB2 - wedgesum)
        Ystd = np.sqrt(Ymeansq - Ymean**2)

        adjsum = np.dot(x, np.dot(A, x)) / 2 - np.dot(x, deg)**2 / (4 * m) + np.dot(x, deg**2) / (4 * m)
        beta = 0.9
        delta = 0.8
        score = k**(-delta) * (adjsum - (Ymean + 1.28 * Ystd) * (k / s)**beta)

    return score


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

    author2sub_ids = {}
    for submission in all_submissions:
        for author_id in submission.content['authorids']['value']:
            if author_id not in author2sub_ids.keys():
                author2sub_ids[author_id] = []
            author2sub_ids[author_id].append(submission.id)

    return author2sub_ids


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run TellTail algorithm')
    parser.add_argument('--bids', type=str, default='ICML2025/data/numeric_bids.csv')

    args = parser.parse_args()

    bids = pd.read_csv(args.bids, header=None, index_col=None)

    all_submission_ids = bids[0].unique()
    all_reviewer_ids = bids[1].unique()

    rev2bids = {rev_id: [] for rev_id in all_reviewer_ids}
    for i, row in bids.iterrows():
        sub_id, rev_id, bid = row
        if bid > 0:
            rev2bids[rev_id].append(sub_id)

    authors2sub_ids = get_authors()
    # add reviewers that are not authors to this list
    for rev_id in all_reviewer_ids:
        if rev_id not in authors2sub_ids.keys():
            authors2sub_ids[rev_id] = []

    # Build the reviewer-reviewer matrix.
    rev_rev_matrix = np.zeros((len(all_reviewer_ids), len(all_reviewer_ids)))
    rev_id2index = {}
    rev_index2id = {}
    for index, rev_id in enumerate(all_reviewer_ids):
        rev_id2index[rev_id] = index
        rev_index2id[index] = rev_id

    for rev1 in all_reviewer_ids:
        for rev2 in all_reviewer_ids:
            edge = len(list(set(rev2bids[rev1]) & set(authors2sub_ids[rev2]))) > 0
            rev_rev_matrix[rev_id2index[rev1], rev_id2index[rev2]] = edge

    # DEBUGGING
    print("WARNING: Using a random graph for debugging.")
    rev_rev_matrix = np.random.binomial(n=1, p=0.5, size=(10,10))

    print("Number of edges in the directed graph:", rev_rev_matrix.sum())
    print("Number of edges in the undirected graph:", (rev_rev_matrix * rev_rev_matrix.T).sum())

    # Run TellTail algorithm
    rng_init = np.random.RandomState(SEED)
    start_v = get_local_search_init(rev_rev_matrix)
    #start_v = np.argmax(rev_rev_matrix.sum(axis=0))  # Hack
    S_detect, method_param_string = run_telltail(rev_rev_matrix, start_v, rng_init)

    S_detect_ids = [rev_index2id[index] for index in S_detect]
    print("Potential colluders:", S_detect_ids)

"""
I'm facing this error when using the ICML2024 subset of bids... but code runs with a random graph

/home/mila/l/lachaseb/openreview-matcher/ICML2025/scripts/telltail.py:68: RuntimeWarning: invalid value encountered in divide
  M = A - np.outer(d, d) / (2 * m)
/home/mila/l/lachaseb/openreview-matcher/ICML2025/scripts/telltail.py:142: RuntimeWarning: invalid value encountered in scalar divide
  sumB = np.sum(deg**2) / (4 * m)
/home/mila/l/lachaseb/openreview-matcher/ICML2025/scripts/telltail.py:143: RuntimeWarning: invalid value encountered in scalar divide
  sumB2 = m + (np.sum(deg**2)**2 - np.sum(deg**4)) / (8 * m**2) - np.dot(deg, np.dot(A, deg)) / (2 * m)
/home/mila/l/lachaseb/openreview-matcher/ICML2025/scripts/telltail.py:144: RuntimeWarning: invalid value encountered in divide
  sumBrow2 = np.sum((deg**2 / (2 * m))**2)
/home/mila/l/lachaseb/openreview-matcher/ICML2025/scripts/telltail.py:155: RuntimeWarning: invalid value encountered in scalar divide
  adjsum = np.dot(x, np.dot(A, x)) / 2 - np.dot(x, deg)**2 / (4 * m) + np.dot(x, deg**2) / (4 * m)
-> del
Traceback (most recent call last):
  File "/home/mila/l/lachaseb/openreview-matcher/ICML2025/scripts/telltail.py", line 240, in <module>
    S_detect, method_param_string = run_telltail(rev_rev_matrix, start_v, rng_init)
  File "/home/mila/l/lachaseb/openreview-matcher/ICML2025/scripts/telltail.py", line 58, in run_telltail
    result = detect_telltail(G_undir, S_start)
  File "/home/mila/l/lachaseb/openreview-matcher/ICML2025/scripts/telltail.py", line 125, in detect_telltail
    deg = deg - M[:, idx_del].reshape(-1, 1)
ValueError: operands could not be broadcast together with shapes (2208,1) (4875264,1)
"""