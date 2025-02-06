import openreview
import pandas as pd
import os
import argparse
import time
import json
import warnings

warnings.filterwarnings("ignore")

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

def post_score_edges(intivation_name, affinity_scores, match_group):

    invitation = f'ICML.cc/2025/Conference/{match_group}/-/{intivation_name}'
    
    if match_group == 'Reviewers':
        readers = ['ICML.cc/2025/Conference','ICML.cc/2025/Conference/Senior_Area_Chairs','ICML.cc/2025/Conference/Area_Chairs']
    elif match_group == 'Area_Chairs':
        readers = ['ICML.cc/2025/Conference']
    else:
        raise ValueError(f"Unknown match group: {match_group}")

    print(f"\nPosting {len(affinity_scores)} affinity scores for {match_group}")
    
    rev_edges=[]
    for _,row in affinity_scores.iterrows():
        rev_edges.append(openreview.Edge(
                                invitation=invitation,
                                head=row[0],
                                tail=row[1],
                                weight=row[2],
                                readers=readers+[row[1]],
                                nonreaders=[],
                                writers=['ICML.cc/2025/Conference'],
                                signatures=['ICML.cc/2025/Conference']
                                ))

    post=openreview.tools.post_bulk_edges(CLIENT_V2, rev_edges)

    print(f"Posted {len(rev_edges)} area chair affinity scores")


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

def post_assignments(assignment_title, assignment_file, match_group):

    print(f"\nPosting {match_group} assignments from {assignment_file}")
    assignment_dict=json.load(open(assignment_file))

    active_submissions = CLIENT_V2.get_all_notes(content={'venueid': 'ICML.cc/2025/Conference/Submission'})
    forum_number={s.id:s.number for s in active_submissions} # map paper forum id to paper number

    if match_group == 'Reviewers':
        assignment_edges, score_edges = set_rev_assignments(assignment_dict, forum_number, assignment_title, CONFERENCE_ID)
    elif match_group == 'Area_Chairs':
        assignment_edges, score_edges = set_ac_assignments(assignment_dict, forum_number, assignment_title, CONFERENCE_ID)
    else:
        raise ValueError(f"Unknown match group: {match_group}")

    post=openreview.tools.post_bulk_edges(CLIENT_V2, assignment_edges)
    post=openreview.tools.post_bulk_edges(CLIENT_V2, score_edges)

    print(f"Posted {len(assignment_edges)} {match_group} assignments")

def delete_invitation(invitation_name, match_group='Reviewers'):
    
    score_edge_invitation = f'ICML.cc/2025/Conference/{match_group}/-/{invitation_name}'

    rev_edges = CLIENT_V2.get_grouped_edges(invitation=score_edge_invitation, groupby='tail', select='head,weight')
    print(f"Found {len(rev_edges)} scores in invitation {score_edge_invitation}")

    if len(rev_edges) > 0:
        CLIENT_V2.delete_edges(invitation=score_edge_invitation)

        while len(rev_edges) > 0:
            # Wait and check again
            time.sleep(30)
            rev_edges = CLIENT_V2.get_grouped_edges(invitation=score_edge_invitation, groupby='tail', select='head,weight')
            print(f"Found {len(rev_edges)} scores still in the invitation")

        print(f"Deleted previous scores")
        

    else:
        print(f"No previous scores to delete")

def delete_assignments(assignment_title, match_group='Reviewers'):
    
    assignment_invitation = f'ICML.cc/2025/Conference/{match_group}/-/Proposed_Assignment'

    edges = CLIENT_V2.get_grouped_edges(invitation=assignment_invitation, label=assignment_title, groupby='tail', select='head,weight')
    print(f"Found {len(edges)} assignments in invitation {assignment_invitation} with label {assignment_title}")
    
    if len(edges) > 0:
        CLIENT_V2.delete_edges(label=assignment_title, invitation=assignment_invitation)

        while len(edges) > 0:
            # Wait and check again
            time.sleep(30)
            edges = CLIENT_V2.get_grouped_edges(invitation=assignment_invitation, label=assignment_title, groupby='tail', select='head,weight')
            print(f"Found {len(edges)} assignments still in the invitation")

        print(f"Deleted previous assignments")

    else:
        print(f"No previous assignments to delete")

if __name__ == '__main__':
    """
    Example usage:

    module load anaconda
    conda activate openreview-matcher

    export OPENREVIEW_USERNAME=''
    export OPENREVIEW_PASSWORD=''

    export GROUP='Area_Chairs'
    export ROOT_FOLDER=$SCRATCH/ICML2025/$GROUP

    # Upload affinity scores
    python ICML2025/scripts/upload_results.py \
        --invitation_name Affinity_Score \
        --match_group $GROUP \
        --ac_affinity_file $ROOT_FOLDER/aggregated_scores_max.csv \
        --k 400

    # Upload assignments
    export jobid=6051552
    python ICML2025/scripts/upload_results.py \
        --match_group $GROUP \
        --assignment_title "Emphasizing_quantiles_(.75-.7-.7)" \
        --assignment_file $ROOT_FOLDER/jobs/$jobid/assignments/assignments.json
    

    """

    args = argparse.ArgumentParser()
    args.add_argument('--invitation_name', type=str, required=False, help='Name of the invitation')
    args.add_argument('--match_group', type=str, required=False, help='Match group (Reviewers or Area_Chairs)')
    args.add_argument('--affinity_file', type=str, required=False, help='Path to the area chair affinity file')
    args.add_argument('--k', type=int, required=False, help='Top k scores to keep')

    args.add_argument('--assignment_title', type=str, required=False, help='Title of the assignment')
    args.add_argument('--assignment_file', type=str, required=False, help='Path to the reviewer assignment file')


    args = args.parse_args()

    start_time = time.time()

    # # -----------------------------------------------------------------
    # # Delete previous scores
    # # -----------------------------------------------------------------
    
    # print(f"\nDeleting previous scores for {args.match_group} under invitation {args.invitation_name}")
    # delete_invitation(args.invitation_name, match_group=args.match_group)

    # # -----------------------------------------------------------------
    # # Create invitations for uploading affinity scores. 
    # # -----------------------------------------------------------------
    
    # print(f"\nCreating invitation {args.invitation_name}")

    # create_invitation(args.invitation_name)

    # print(f"Invitation {args.invitation_name} created")

    # # -----------------------------------------------------------------
    # # Upload affinity scores
    # # -----------------------------------------------------------------

    # # Filter top k scores
    # top_scores = top_k_scores(args.affinity_file, args.k)

    # # Post affinity scores
    # post_score_edges(args.invitation_name, top_scores, match_group=args.match_group)


    # # -----------------------------------------------------------------
    # # Delete previous assignments
    # # -----------------------------------------------------------------
    
    # print(f"\nDeleting previous assignments for {args.match_group} under title {args.assignment_title}")
    # delete_assignments(args.assignment_title, match_group=args.match_group)

    # # -----------------------------------------------------------------
    # # Upload assignments
    # # -----------------------------------------------------------------

    # print(f"\nUploading assignments...")
    # post_assignments(args.assignment_title, args.assignment_file, match_group=args.match_group)


    print(f"\nDone. Elapsed time: {time.time()-start_time:.2f} seconds")