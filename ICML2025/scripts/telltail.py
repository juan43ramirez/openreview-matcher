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

def run_telltail(G, start_v, rng_init, graph_type='intersection'):
    if np.any(G != G.T):
        if graph_type == 'intersection':
            G_undir = np.clip(G * G.T, 0, 1)
        elif graph_type == "union":
            G_undir = np.clip(G + G.T, 0, 1)
        else:
            raise NotImplementedError("graph_type must be 'intersection' or 'union' when G != G.T")
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
    #print("# submissions from the v2 API:", len(submissions_v2))

    author2sub_ids = {}
    all_submission_ids = []
    for submission in all_submissions:
        all_submission_ids.append(submission.id)
        for author_id in submission.content['authorids']['value']:
            if author_id not in author2sub_ids.keys():
                author2sub_ids[author_id] = []
            author2sub_ids[author_id].append(submission.id)

    return author2sub_ids, np.unique(all_submission_ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run TellTail algorithm')
    parser.add_argument('--bids', type=str, default='ICML2025/data/numeric_bids.csv')
    #parser.add_argument('--filtered_file', type=str, default='ICML2025/data/filtered_numeric_bids.csv')
    parser.add_argument('--undirected_type', type=str, default='union', choices=['union', 'intersection'])

    args = parser.parse_args()
    folder = args.bids.replace(os.path.basename(args.bids), '')

    bids = pd.read_csv(args.bids, header=None, index_col=None)

    total_num_bids = len(bids)
    all_submission_ids = bids[0].unique()
    all_reviewer_ids = bids[1].unique()

    rev2bids = {rev_id: [] for rev_id in all_reviewer_ids}
    for i, row in bids.iterrows():
        sub_id, rev_id, bid = row
        if bid > 0:
            rev2bids[rev_id].append(sub_id)

    authors2sub_ids, all_submission_ids_ = get_authors()
    print("Number of reviewers (bid file):", len(set(all_reviewer_ids)))
    print("Number of authors (API):", len(authors2sub_ids))
    print("Intersection of the above two:", len(set(authors2sub_ids.keys()) & set(all_reviewer_ids)))
    print("Number of Submissions (API):", len(all_submission_ids_))
    print("Number of Submissions (bid file):", len(all_submission_ids))
    print("Intersection of the above two:", len(set(all_submission_ids) & set(all_submission_ids_)))

    # add reviewers that are not authors to this list
    for rev_id in all_reviewer_ids:
        if rev_id not in authors2sub_ids.keys():
            authors2sub_ids[rev_id] = []
        #else:
        #    print(f"reviewer {rev_id} authored a submission.")

    # Build the reviewer-reviewer matrix.
    rev_id2index = {}
    rev_index2id = {}
    for index, rev_id in enumerate(all_reviewer_ids):
        rev_id2index[rev_id] = index
        rev_index2id[index] = rev_id

    revrev2sub_ids = {}
    rev_rev_matrix = np.zeros((len(all_reviewer_ids), len(all_reviewer_ids)))
    for rev1 in all_reviewer_ids:
        for rev2 in all_reviewer_ids:
            revrev2sub_ids[(rev1, rev2)] = set(rev2bids[rev1]) & set(authors2sub_ids[rev2])  # papers of rev2 on which rev1 bidded
            rev_rev_matrix[rev_id2index[rev1], rev_id2index[rev2]] = len(revrev2sub_ids[(rev1, rev2)]) > 0
            if rev1 == rev2: assert len(revrev2sub_ids[(rev1, rev2)]) == 0

    # DEBUGGING
    #print("WARNING: Using a random graph for debugging.")
    #rev_rev_matrix = np.random.binomial(n=1, p=0.5, size=(10,10))

    num_trials = 10
    all_suspicious_bids = []
    all_suspicious_bids_set = set([])
    all_suspicious_rev = []
    for trial in range(num_trials):
        print(f"Trial #{trial}")
        print("Number of edges in the directed graph:", rev_rev_matrix.sum())
        print("Number of edges in the undirected graph (intersect):", (rev_rev_matrix * rev_rev_matrix.T).sum())
        print("Number of edges in the undirected graph (union):", ((rev_rev_matrix + rev_rev_matrix.T) > 0).sum())
        #print("Number of reviewers:", rev_rev_matrix.shape[0])

        # Run TellTail algorithm
        rng_init = np.random.RandomState(SEED)
        start_v = get_local_search_init(rev_rev_matrix)
        #start_v = np.argmax(rev_rev_matrix.sum(axis=0))  # Hack
        print("Running TellTail...")
        S_detect, method_param_string = run_telltail(rev_rev_matrix, start_v, rng_init, graph_type=args.undirected_type)
        suspicious_rev_ids = [rev_index2id[index] for index in S_detect]
        all_suspicious_rev.append(suspicious_rev_ids)
        print("Potential colluders:", suspicious_rev_ids)

        # remove bids from the rev_rev_matrix for the next trial
        for suspicious_index in S_detect:
            rev_rev_matrix[suspicious_index, S_detect] = 0

        # record suspicious bids
        suspicious_bids = []
        for rev1 in suspicious_rev_ids:
            for rev2 in suspicious_rev_ids:
                for sub_id in revrev2sub_ids[(rev1,rev2)]:
                    suspicious_bids.append((sub_id, rev1))
        all_suspicious_bids.append(set(suspicious_bids))
        all_suspicious_bids_set = all_suspicious_bids_set | set(suspicious_bids)

        print(f"Number of bids removed: {len(all_suspicious_bids_set)}/{total_num_bids}")
        if len(all_suspicious_bids_set) >= 0.01 * total_num_bids:
            break

    # producing list of removed bids
    filename = os.path.join(folder, "removed_bids.csv")
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, "w", newline='') as file:
        for trial in range(len(all_suspicious_bids)):
            file.write(f"Trial #{trial}")
            file.write('\n')
            for suspicious_bid in all_suspicious_bids[trial]:
                sub_id, rev_id = suspicious_bid
                file.write(f"{sub_id},{rev_id}")
                file.write('\n')

    # producing filtered csv file
    filename = os.path.join(folder, "filtered_bids.csv")
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, "w", newline='') as file:
        for i, row in bids.iterrows():
            sub_id, rev_id, bid = row
            if (sub_id,rev_id) in all_suspicious_bids:
                print("Dropping line:", sub_id, rev_id, bid)
            else:
                file.write(f"{sub_id},{rev_id},{bid}")
                file.write('\n')


"""
HOW TO USE:
- Might want to change the CONFERENCE_ID on line 12 to "2025".
- Give path to cvs file containing bids via the --bids argument.
- Code will produce two files in the folder containing the bid csv file: 
    - removed_bids.csv : List of bids that were removed at each trial.
    - filtered_bids.csv : List of original bids but without suspicious bids.
"""



"""
I'm facing this error when using the ICML2024 subset of bids... 
Code runs with a random graph (changing to 'union' instead of 'intersection' also worked) 

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