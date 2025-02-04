import openreview
import pandas as pd
import os
import argparse
import time
import json

# Use environment variables to store the username and password
OR_USERNAME = os.environ.get('OPENREVIEW_USERNAME')
OR_PASSWORD = os.environ.get('OPENREVIEW_PASSWORD')

CONFERENCE_ID = 'ICML.cc/2025/Conference'

CLIENT_V2 = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username=OR_USERNAME,
    password=OR_PASSWORD
)


def create_invitation(name):
    """Create an invitation for uploading affinity scores"""

    rev_invitation = openreview.api.Invitation(
        id=f'ICML.cc/2025/Conference/Reviewers/-/{name}',
        invitees=['ICML.cc/2025/Conference'],
        readers=['ICML.cc/2025/Conference','ICML.cc/2025/Conference/Senior_Area_Chairs', 'ICML.cc/2025/Conference/Area_Chairs'],
        writers=['ICML.cc/2025/Conference'],
        signatures=['ICML.cc/2025/Conference'],
        type='Edge',
        edit={
    "id": {
        "param": {
        "withInvitation": f"ICML.cc/2025/Conference/Reviewers/-/{name}",
        "optional": True
        }
    },
    "ddate": {
        "param": {
        "range": [
            0,
            9999999999999
        ],
        "optional": True,
        "deletable": True
        }
    },
    "cdate": {
        "param": {
        "range": [
            0,
            9999999999999
        ],
        "optional": True,
        "deletable": True
        }
    },
    "readers": [
        "ICML.cc/2025/Conference",
        "ICML.cc/2025/Conference/Senior_Area_Chairs",
        "ICML.cc/2025/Conference/Area_Chairs",
        "${2/tail}"
    ],
    "nonreaders": [
        "ICML.cc/2025/Conference/Submission${{2/head}/number}/Authors"
    ],
    "writers": [
        "ICML.cc/2025/Conference"
    ],
    "signatures": {
        "param": {
        "regex": "ICML.cc/2025/Conference$|ICML.cc/2025/Conference/Program_Chairs",
        "default": [
            "ICML.cc/2025/Conference/Program_Chairs"
        ]
        }
    },
    "head": {
        "param": {
        "type": "note",
        "withInvitation": "ICML.cc/2025/Conference/-/Submission"
        }
    },
    "tail": {
        "param": {
        "type": "profile",
        "options": {
            "group": "ICML.cc/2025/Conference/Reviewers"
        }
        }
    },
    "weight": {
        "param": {
        "minimum": -1
        }
    },
    "label": {
        "param": {
        "regex": ".*",
        "optional": True,
        "deletable": True
        }
    }
    }
    )

    post=CLIENT_V2.post_invitation_edit(
        invitations='ICML.cc/2025/Conference/-/Edit',
        signatures=['ICML.cc/2025/Conference'],
        invitation=rev_invitation
    )

    ac_invitation = openreview.api.Invitation(
        id=f'ICML.cc/2025/Conference/Area_Chairs/-/{name}',
        invitees=['ICML.cc/2025/Conference'],
        readers=['ICML.cc/2025/Conference','ICML.cc/2025/Conference/Senior_Area_Chairs'],
        writers=['ICML.cc/2025/Conference'],
        signatures=['ICML.cc/2025/Conference'],
        type='Edge',
        edit={
    "id": {
        "param": {
        "withInvitation": "ICML.cc/2025/Conference/Area_Chairs/-/{name}",
        "optional": True
        }
    },
    "ddate": {
        "param": {
        "range": [
            0,
            9999999999999
        ],
        "optional": True,
        "deletable": True
        }
    },
    "cdate": {
        "param": {
        "range": [
            0,
            9999999999999
        ],
        "optional": True,
        "deletable": True
        }
    },
    "readers": [
        "ICML.cc/2025/Conference",
        "ICML.cc/2025/Conference/Senior_Area_Chairs",
        "${2/tail}"
    ],
    "nonreaders": [
        "ICML.cc/2025/Conference/Submission${{2/head}/number}/Authors"
    ],
    "writers": [
        "ICML.cc/2025/Conference"
    ],
    "signatures": {
        "param": {
        "regex": "ICML.cc/2025/Conference$|ICML.cc/2025/Conference/Program_Chairs",
        "default": [
            "ICML.cc/2025/Conference/Program_Chairs"
        ]
        }
    },
    "head": {
        "param": {
        "type": "note",
        "withInvitation": "ICML.cc/2025/Conference/-/Submission"
        }
    },
    "tail": {
        "param": {
        "type": "profile",
        "options": {
            "group": "ICML.cc/2025/Conference/Area_Chairs"
        }
        }
    },
    "weight": {
        "param": {
        "minimum": -1
        }
    },
    "label": {
        "param": {
        "regex": ".*",
        "optional": True,
        "deletable": True
        }
    }
    }
    )

    post=CLIENT_V2.post_invitation_edit(
        invitations='ICML.cc/2025/Conference/-/Edit',
        signatures=['ICML.cc/2025/Conference'],
        invitation=ac_invitation
    )

def post_score_edges(intivation_name, reviewer_affinity=None, ac_affinity=None):

    if reviewer_affinity is not None:
        print(f"\nPosting affinity scores for {len(reviewer_affinity)} reviewers")

        rev_edges=[]
        for _,row in reviewer_affinity.iterrows():
            rev_edges.append(openreview.Edge(
                                    invitation=f'ICML.cc/2025/Conference/Reviewers/-/{intivation_name}',
                                    head=row[0],
                                    tail=row[1],
                                    weight=row[2],
                                    readers=['ICML.cc/2025/Conference','ICML.cc/2025/Conference/Senior_Area_Chairs','ICML.cc/2025/Conference/Area_Chairs',row[1]],
                                    nonreaders=[],
                                    writers=['ICML.cc/2025/Conference'],
                                    signatures=['ICML.cc/2025/Conference']
                                    ))
        post=openreview.tools.post_bulk_edges(CLIENT_V2, rev_edges)

        print(f"Posted {len(rev_edges)} reviewer affinity scores")

    if ac_affinity is not None:
        print(f"\nPosting affinity scores for {len(ac_affinity)} area chairs")

        ac_edges=[]
        for _,row in ac_affinity.iterrows():
            ac_edges.append(openreview.Edge(
                                    invitation=f'ICML.cc/2025/Conference/Area_Chairs/-/{intivation_name}',
                                    head=row[0],
                                    tail=row[1],
                                    weight=row[2],
                                    readers=['ICML.cc/2025/Conference',row[1]], # if getting readers not match invitation error, try this readers=['ICML.cc/2025/Conference','ICML.cc/2025/Conference/Senior_Area_Chairs',row[1]]
                                    nonreaders=[],
                                    writers=['ICML.cc/2025/Conference'],
                                    signatures=['ICML.cc/2025/Conference']
                                    ))
        post=openreview.tools.post_bulk_edges(CLIENT_V2, ac_edges)

        print(f"Posted {len(ac_edges)} area chair affinity scores")
        
    # Verify the uploaded scores
    print(f"\nVerifying uploaded scores")
    if reviewer_affinity is not None:
        rev_edges = CLIENT_V2.get_edges(invitation=f'ICML.cc/2025/Conference/Reviewers/-/{intivation_name}')
        assert len(rev_edges) == len(top_reviewer_scores), "Some reviewer scores were not uploaded"
        print(f"Found {len(rev_edges)} reviewer scores")

    if ac_affinity is not None:
        ac_edges = CLIENT_V2.get_edges(invitation=f'ICML.cc/2025/Conference/Area_Chairs/-/{intivation_name}')
        assert len(ac_edges) == len(top_ac_scores), "Some area chair scores were not uploaded"
        print(f"Found {len(ac_edges)} area chair scores")

def top_k_scores(affinity_file, k=10):

    if affinity_file is None:
        return None

    print(f"\nReading affinity scores from {affinity_file}")

    df=pd.read_csv(affinity_file, header=None)

    print(f"Read {len(df)} affinity scores")


    print(f"\nKeeping top {k} scores for each submission")
    top_k_submissions = df.groupby(0).apply(lambda x: x.nlargest(k, 2)).reset_index(drop=True)

    print(f"Keeping top {k} scores for each reviewer")
    top_k_reviewers = df.groupby(1).apply(lambda x: x.nlargest(k, 2)).reset_index(drop=True)

    print(f"Concatenating and removing duplicates")
    top_scores = pd.concat([top_k_submissions, top_k_reviewers]).drop_duplicates()

    assert top_scores.groupby(0).size().max() >= k, "Not all papers have k scores"
    assert top_scores.groupby(1).size().max() >= k, "Not all reviewers have k scores"

    num_submissions, num_reviewers = len(top_scores[0].unique()), len(top_scores[1].unique())

    print(f"\nDone. Kept {len(top_scores)} top scores out of {len(df)} original scores for {num_submissions} submissions and {num_reviewers} reviewers")

    return top_scores

def set_rev_assignments(assignments_by_forum, paper_numbers, label, venue_id):

    assignment_edges = []
    score_edges = []

    for forum, assignments in assignments_by_forum.items():
        try:
            paper_number = paper_numbers[forum]
        except KeyError:
            # A paper may have been desk-rejected or withdrawn since the assignment
            continue

        for paper_user_entry in assignments:
            score = paper_user_entry["aggregate_score"]
            user = paper_user_entry["user"]

            assignment_edges.append(
                openreview.Edge(
                    head=forum,
                    tail=user,
                    weight=score,
                    label=label,
                    invitation=f"{venue_id}/Reviewers/-/Proposed_Assignment",
                    readers=[venue_id,f"{venue_id}/Submission{paper_number}/Senior_Area_Chairs",f"{venue_id}/Submission{paper_number}/Area_Chairs",user],
                    nonreaders=[f"{venue_id}/Submission{paper_number}/Authors"],
                    writers=[venue_id,f"{venue_id}/Submission{paper_number}/Senior_Area_Chairs",f"{venue_id}/Submission{paper_number}/Area_Chairs"],
                    signatures=[f"{venue_id}/Program_Chairs"]
                )
            )

            score_edges.append(
                openreview.Edge(
                    head=forum,
                    tail=user,
                    weight=score,
                    label=label,
                    invitation=f"{venue_id}/Reviewers/-/Aggregate_Score",
                    readers=[venue_id,f"{venue_id}/Submission{paper_number}/Senior_Area_Chairs",f"{venue_id}/Submission{paper_number}/Area_Chairs",user],
                    nonreaders=[f"{venue_id}/Submission{paper_number}/Authors"],
                    writers=[venue_id,f"{venue_id}/Submission{paper_number}/Senior_Area_Chairs",f"{venue_id}/Submission{paper_number}/Area_Chairs"],
                    signatures=[f"{venue_id}/Program_Chairs"]
                )
            )
    
    return assignment_edges, score_edges


def set_ac_assignments(assignments_by_forum, paper_numbers, label, venue_id):

    assignment_edges = []
    score_edges = []

    for forum, assignments in assignments_by_forum.items():
        try:
            paper_number = paper_numbers[forum]
        except KeyError:
            # A paper may have been desk-rejected or withdrawn since the assignment
            continue

        for paper_user_entry in assignments:
            score = paper_user_entry["aggregate_score"]
            user = paper_user_entry["user"]

            assignment_edges.append(
                openreview.Edge(
                    head=forum,
                    tail=user,
                    weight=score,
                    label=label,
                    invitation=f"{venue_id}/Area_Chairs/-/Proposed_Assignment",
                    readers=[venue_id,f"{venue_id}/Submission{paper_number}/Senior_Area_Chairs",user],
                    nonreaders=[f"{venue_id}/Submission{paper_number}/Authors"],
                    writers=[venue_id,f"{venue_id}/Submission{paper_number}/Senior_Area_Chairs"],
                    signatures=[f"{venue_id}/Program_Chairs"]
                )
            )

            score_edges.append(
                openreview.Edge(
                    head=forum,
                    tail=user,
                    weight=score,
                    label=label,
                    invitation=f"{venue_id}/Area_Chairs/-/Aggregate_Score",
                    readers=[venue_id,f"{venue_id}/Submission{paper_number}/Senior_Area_Chairs",user],
                    nonreaders=[f"{venue_id}/Submission{paper_number}/Authors"],
                    writers=[venue_id,f"{venue_id}/Submission{paper_number}/Senior_Area_Chairs"],
                    signatures=[f"{venue_id}/Program_Chairs"]
                )
            )
    
    return assignment_edges, score_edges

def post_assignments(assignment_title, assignment_file, match_group='reviewers'):
    assignment_dict=json.load(open(assignment_file))

    active_submissions = CLIENT_V2.get_all_notes(content={'venueid': 'ICML.cc/2025/Conference/Submission'})
    forum_number={s.id:s.number for s in active_submissions} # map paper forum id to paper number

    if match_group == 'reviewers':
        assignment_edges, score_edges = set_rev_assignments(assignment_dict, forum_number, assignment_title, CONFERENCE_ID)
    elif match_group == 'area_chairs':
        assignment_edges, score_edges = set_ac_assignments(assignment_dict, forum_number, assignment_title, CONFERENCE_ID)
    else:
        raise ValueError(f"Unknown match group: {match_group}")

    post=openreview.tools.post_bulk_edges(CLIENT_V2, assignment_edges)
    post=openreview.tools.post_bulk_edges(CLIENT_V2, score_edges)
    
    return assignment_edges, score_edges

def delete_invitation(invitation_name):
    CLIENT_V2.delete_edges(invitation=f'ICML.cc/2025/Conference/Reviewers/-/{invitation_name}')
    CLIENT_V2.delete_edges(invitation=f'ICML.cc/2025/Conference/Area_Chairs/-/{invitation_name}')

if __name__ == '__main__':
    """
    Example usage:

    python ICML2025/scripts/upload_results.py \
        --invitation_name robust_affinity_Q75 \
        --reviewer_affinity_file $ROOT_FOLDER/robust_affinity_Q75.csv \
        --k 50 \
        --reviewer_assignment_title Test-visualization-first-3-Q75 \
        --reviewer_assignment_file $ROOT_FOLDER/assignments/first_matching.json
    """

    args = argparse.ArgumentParser()
    args.add_argument('--invitation_name', type=str, required=True, help='Name of the invitation')
    args.add_argument('--reviewer_affinity_file', type=str, required=False, help='Path to the reviewer affinity file')
    args.add_argument('--ac_affinity_file', type=str, required=False, help='Path to the area chair affinity file')
    args.add_argument('--k', type=int, required=False, help='Top k scores to keep')

    args.add_argument('--reviewer_assignment_title', type=str, required=False, help='Title of the assignment')
    args.add_argument('--reviewer_assignment_file', type=str, required=False, help='Path to the reviewer assignment file')

    args.add_argument('--ac_assignment_title', type=str, required=False, help='Title of the assignment')
    args.add_argument('--ac_assignment_file', type=str, required=False, help='Path to the area chair assignment file')

    args = args.parse_args()

    start_time = time.time()

    # -----------------------------------------------------------------
    # Upload affinity scores
    # -----------------------------------------------------------------

    # # Delete previous invitation. Commented out to keep history of previous uploads
    # delete_invitation(args.invitation_name)

    # Create invitations for uploading affinity scores. Hard-deleting the previous
    # invitation first
    print(f"\nCreating invitation {args.invitation_name}")
    create_invitation(args.invitation_name)
    print(f"Invitation {args.invitation_name} created")

    # Filter top k scores
    top_reviewer_scores = top_k_scores(args.reviewer_affinity_file, args.k)
    top_ac_scores = top_k_scores(args.ac_affinity_file, args.k)

    # Post affinity scores
    post_score_edges(args.invitation_name, top_reviewer_scores, top_ac_scores)

    # -----------------------------------------------------------------
    # Upload assignments
    # -----------------------------------------------------------------
    print(f"\nUploading assignments...")

    # ----------------------- Reviewers -----------------------
    if args.reviewer_assignment_file is not None:
        print(f"\nReading reviewer assignments from {args.reviewer_assignment_file}")
        rev_assignment_edges, rev_score_edges = post_assignments(
            args.reviewer_assignment_title, args.reviewer_assignment_file, match_group='reviewers'
            )
        print(f"Posted {len(rev_assignment_edges)} reviewer assignments")

    # ----------------------- Area Chairs -----------------------
    if args.ac_assignment_file is not None:
        print(f"\nReading area chair assignments from {args.ac_assignment_file}")
        ac_assignment_edges, ac_score_edges = post_assignments(
            args.ac_assignment_title, args.ac_assignment_file, match_group='area_chairs'
            )
        print(f"Posted {len(ac_assignment_edges)} area chair assignments")

    print(f"\nElapsed time: {time.time()-start_time:.2f} seconds")