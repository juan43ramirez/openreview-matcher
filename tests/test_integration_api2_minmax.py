"""
End-to-end integration tests with OpenReview server.
"""

import json

import openreview
from openreview.api import Note
import pytest

from conftest import clean_start_conference_v2, wait_for_status


def test_integration_basic(openreview_context, celery_app, celery_session_worker):
    """
    Basic integration test. Makes use of the OpenReview Builder
    """

    openreview_client = openreview_context["openreview_client_v2"]
    test_client = openreview_context["test_client"]

    conference_id = "ICLS.cc/2019/Conference"
    num_reviewers = 10
    num_papers = 10
    reviews_per_paper = 3
    max_papers = 5
    min_papers = 1
    alternates = 0

    venue = clean_start_conference_v2(
        openreview_client,
        conference_id,
        num_reviewers,
        num_papers,
        reviews_per_paper,
    )

    reviewers_id = venue.get_reviewers_id()

    config = {
        "title": {"value": "integration-test"},
        "user_demand": {"value": str(reviews_per_paper)},
        "max_papers": {"value": str(max_papers)},
        "min_papers": {"value": str(min_papers)},
        "alternates": {"value": str(alternates)},
        "config_invitation": {
            "value": "{}/-/Assignment_Configuration".format(reviewers_id)
        },
        "paper_invitation": {"value": venue.get_submission_id()},
        "assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id)
        },
        "deployed_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, deployed=True)
        },
        "invite_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, invite=True)
        },
        "aggregate_score_invitation": {
            "value": "{}/-/Aggregate_Score".format(reviewers_id)
        },
        "conflicts_invitation": {
            "value": venue.get_conflict_score_id(reviewers_id)
        },
        "custom_max_papers_invitation": {
            "value": "{}/-/Custom_Max_Papers".format(reviewers_id)
        },
        "match_group": {"value": reviewers_id},
        "scores_specification": {
            "value": {
                venue.get_affinity_score_id(reviewers_id): {
                    "weight": 1.0,
                    "default": 0.0,
                }
            }
        },
        "status": {"value": "Initialized"},
        "solver": {"value": "MinMax"},
    }

    config_note = openreview_client.post_note_edit(
        invitation="{}/-/Assignment_Configuration".format(reviewers_id),
        signatures=[venue.get_id()],
        note=Note(content=config),
    )
    assert config_note

    response = test_client.post(
        "/match",
        data=json.dumps({"configNoteId": config_note["note"]["id"]}),
        content_type="application/json",
        headers=openreview_client.headers,
    )
    assert response.status_code == 200

    matcher_status = wait_for_status(
        openreview_client, config_note["note"]["id"], api_version=2
    )
    assert matcher_status.content["status"]["value"] == "Complete"

    paper_assignment_edges = openreview_client.get_edges_count(
        label="integration-test",
        invitation=venue.get_assignment_id(venue.get_reviewers_id()),
    )

    assert paper_assignment_edges == num_papers * reviews_per_paper


def test_integration_no_solution_due_to_conflicts(
    openreview_context, celery_app, celery_session_worker
):
    """
    Basic integration test. Makes use of the OpenReview Builder
    """
    openreview_client = openreview_context["openreview_client_v2"]
    test_client = openreview_context["test_client"]

    conference_id = "ICLS.cca/2020/Conference"
    num_reviewers = 3
    num_papers = 1
    reviews_per_paper = 3
    max_papers = 1
    min_papers = 1
    alternates = 0

    venue = clean_start_conference_v2(
        openreview_client,
        conference_id,
        num_reviewers,
        num_papers,
        reviews_per_paper,
    )

    reviewers_id = venue.get_reviewers_id()

    config = {
        "title": {"value": "integration-test"},
        "user_demand": {"value": str(reviews_per_paper)},
        "max_papers": {"value": str(max_papers)},
        "min_papers": {"value": str(min_papers)},
        "alternates": {"value": str(alternates)},
        "config_invitation": {
            "value": "{}/-/Assignment_Configuration".format(reviewers_id)
        },
        "paper_invitation": {"value": venue.get_submission_id()},
        "assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id)
        },
        "deployed_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, deployed=True)
        },
        "invite_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, invite=True)
        },
        "aggregate_score_invitation": {
            "value": "{}/-/Aggregate_Score".format(reviewers_id)
        },
        "conflicts_invitation": {
            "value": venue.get_conflict_score_id(reviewers_id)
        },
        "custom_max_papers_invitation": {
            "value": "{}/-/Custom_Max_Papers".format(reviewers_id)
        },
        "match_group": {"value": reviewers_id},
        "scores_specification": {
            "value": {
                venue.get_affinity_score_id(reviewers_id): {
                    "weight": 1.0,
                    "default": 0.0,
                }
            }
        },
        "status": {"value": "Initialized"},
        "solver": {"value": "MinMax"},
    }

    for reviewer in openreview_client.get_group(reviewers_id).members:
        openreview_client.post_edge(
            openreview.api.Edge(
                invitation=venue.get_conflict_score_id(reviewers_id),
                label="Personal",
                weight=-1,
                head=venue.get_submissions()[-1].id,
                tail=reviewer,
                signatures=[venue.id],
                readers=[venue.id, venue.get_area_chairs_id(), reviewer],
                writers=[venue.id],
            )
        )

    config_note = openreview_client.post_note_edit(
        invitation="{}/-/Assignment_Configuration".format(reviewers_id),
        signatures=[venue.get_id()],
        note=Note(content=config),
    )
    assert config_note

    response = test_client.post(
        "/match",
        data=json.dumps({"configNoteId": config_note["note"]["id"]}),
        content_type="application/json",
        headers=openreview_client.headers,
    )
    assert response.status_code == 200

    matcher_status = wait_for_status(
        openreview_client, config_note["note"]["id"], api_version=2
    )
    assert matcher_status.content["status"]["value"] == "No Solution"
    assert (
        matcher_status.content["error_message"]["value"]
        == "Solver could not find a solution. Try (1) increasing max papers (2) adding more reviewers or (3) using only more recent history for computing conflicts in the Paper Matching Setup to reduce conflicts."
    )

    paper_assignment_edges = openreview_client.get_edges_count(
        label="integration-test",
        invitation=venue.get_assignment_id(venue.get_reviewers_id()),
    )

    assert paper_assignment_edges == 0


def test_integration_supply_mismatch_error(
    openreview_context, celery_app, celery_session_worker
):
    """
    Basic integration test. Makes use of the OpenReview Builder
    """
    openreview_client = openreview_context["openreview_client_v2"]
    test_client = openreview_context["test_client"]

    conference_id = "ICLS.cc/2020/Conference"
    num_reviewers = 10
    num_papers = 10
    reviews_per_paper = 10  # impossible!
    max_papers = 1
    min_papers = 1
    alternates = 0

    venue = clean_start_conference_v2(
        openreview_client,
        conference_id,
        num_reviewers,
        num_papers,
        reviews_per_paper,
    )

    reviewers_id = venue.get_reviewers_id()

    config = {
        "title": {"value": "integration-test-2"},
        "user_demand": {"value": str(reviews_per_paper)},
        "max_papers": {"value": str(max_papers)},
        "min_papers": {"value": str(min_papers)},
        "alternates": {"value": str(alternates)},
        "config_invitation": {
            "value": "{}/-/Assignment_Configuration".format(reviewers_id)
        },
        "paper_invitation": {"value": venue.get_submission_id()},
        "assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id)
        },
        "deployed_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, deployed=True)
        },
        "invite_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, invite=True)
        },
        "aggregate_score_invitation": {
            "value": "{}/-/Aggregate_Score".format(reviewers_id)
        },
        "conflicts_invitation": {
            "value": venue.get_conflict_score_id(reviewers_id)
        },
        "custom_max_papers_invitation": {
            "value": "{}/-/Custom_Max_Papers".format(reviewers_id)
        },
        "match_group": {"value": reviewers_id},
        "scores_specification": {
            "value": {
                venue.get_affinity_score_id(reviewers_id): {
                    "weight": 1.0,
                    "default": 0.0,
                }
            }
        },
        "status": {"value": "Initialized"},
        "solver": {"value": "MinMax"},
    }

    config_note = openreview_client.post_note_edit(
        invitation="{}/-/Assignment_Configuration".format(reviewers_id),
        signatures=[venue.get_id()],
        note=Note(content=config),
    )
    assert config_note

    response = test_client.post(
        "/match",
        data=json.dumps({"configNoteId": config_note["note"]["id"]}),
        content_type="application/json",
        headers=openreview_client.headers,
    )
    assert response.status_code == 200

    matcher_status = wait_for_status(
        openreview_client, config_note["note"]["id"], api_version=2
    )
    assert matcher_status.content["status"]["value"] == "No Solution"
    assert (
        matcher_status.content["error_message"]["value"]
        == "Review demand (100) must be between the min review supply is (10) and max review supply is (10). Try (1) decreasing min papers (2) increasing max papers or (3) finding more reviewers"
    )

    paper_assignment_edges = openreview_client.get_edges_count(
        label="integration-test-2",
        invitation=venue.get_assignment_id(venue.get_reviewers_id()),
    )

    assert paper_assignment_edges == 0


def test_integration_demand_out_of_supply_range_error(
    openreview_context, celery_app, celery_session_worker
):
    """
    Test to check that a No Solution is observed when demand is not in the range of min and max supply
    """
    openreview_client = openreview_context["openreview_client_v2"]
    test_client = openreview_context["test_client"]

    conference_id = "ICLS.cc/2030/Conference"
    num_reviewers = 10
    num_papers = 10
    reviews_per_paper = 3
    max_papers = 5
    min_papers = 4
    alternates = 0

    venue = clean_start_conference_v2(
        openreview_client,
        conference_id,
        num_reviewers,
        num_papers,
        reviews_per_paper,
    )

    reviewers_id = venue.get_reviewers_id()

    config = {
        "title": {"value": "integration-test"},
        "user_demand": {"value": str(reviews_per_paper)},
        "max_papers": {"value": str(max_papers)},
        "min_papers": {"value": str(min_papers)},
        "alternates": {"value": str(alternates)},
        "config_invitation": {
            "value": "{}/-/Assignment_Configuration".format(reviewers_id)
        },
        "paper_invitation": {"value": venue.get_submission_id()},
        "assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id)
        },
        "deployed_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, deployed=True)
        },
        "invite_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, invite=True)
        },
        "aggregate_score_invitation": {
            "value": "{}/-/Aggregate_Score".format(reviewers_id)
        },
        "conflicts_invitation": {
            "value": venue.get_conflict_score_id(reviewers_id)
        },
        "custom_max_papers_invitation": {
            "value": "{}/-/Custom_Max_Papers".format(reviewers_id)
        },
        "match_group": {"value": reviewers_id},
        "scores_specification": {
            "value": {
                venue.get_affinity_score_id(reviewers_id): {
                    "weight": 1.0,
                    "default": 0.0,
                }
            }
        },
        "status": {"value": "Initialized"},
        "solver": {"value": "MinMax"},
    }

    config_note = openreview_client.post_note_edit(
        invitation="{}/-/Assignment_Configuration".format(reviewers_id),
        signatures=[venue.get_id()],
        note=Note(content=config),
    )
    assert config_note

    response = test_client.post(
        "/match",
        data=json.dumps({"configNoteId": config_note["note"]["id"]}),
        content_type="application/json",
        headers=openreview_client.headers,
    )
    assert response.status_code == 200

    matcher_status = wait_for_status(
        openreview_client, config_note["note"]["id"], api_version=2
    )
    assert matcher_status.content["status"]["value"] == "No Solution"
    assert (
        matcher_status.content["error_message"]["value"]
        == "Review demand (30) must be between the min review supply is (40) and max review supply is (50). Try (1) decreasing min papers (2) increasing max papers or (3) finding more reviewers"
    )

    paper_assignment_edges = openreview_client.get_edges_count(
        label="integration-test",
        invitation=venue.get_assignment_id(venue.get_reviewers_id()),
    )

    assert paper_assignment_edges == 0


def test_integration_no_scores(openreview_context, celery_app, celery_session_worker):
    """
    Basic integration test. Makes use of the OpenReview Builder
    """
    openreview_client = openreview_context["openreview_client_v2"]
    test_client = openreview_context["test_client"]

    conference_id = "ICLS.cc/2021/Conference"
    num_reviewers = 10
    num_papers = 10
    reviews_per_paper = 3
    max_papers = 5
    min_papers = 1
    alternates = 0

    venue = clean_start_conference_v2(
        openreview_client,
        conference_id,
        num_reviewers,
        num_papers,
        reviews_per_paper,
    )

    reviewers_id = venue.get_reviewers_id()

    config = {
        "title": {"value": "integration-test"},
        "user_demand": {"value": str(reviews_per_paper)},
        "max_papers": {"value": str(max_papers)},
        "min_papers": {"value": str(min_papers)},
        "alternates": {"value": str(alternates)},
        "config_invitation": {
            "value": "{}/-/Assignment_Configuration".format(reviewers_id)
        },
        "paper_invitation": {"value": venue.get_submission_id()},
        "assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id)
        },
        "deployed_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, deployed=True)
        },
        "invite_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, invite=True)
        },
        "aggregate_score_invitation": {
            "value": "{}/-/Aggregate_Score".format(reviewers_id)
        },
        "conflicts_invitation": {
            "value": venue.get_conflict_score_id(reviewers_id)
        },
        "custom_max_papers_invitation": {
            "value": "{}/-/Custom_Max_Papers".format(reviewers_id)
        },
        "match_group": {"value": reviewers_id},
        "status": {"value": "Initialized"},
        "solver": {"value": "MinMax"},
        "allow_zero_score_assignments": {"value": "Yes"},
    }

    config_note = openreview_client.post_note_edit(
        invitation="{}/-/Assignment_Configuration".format(reviewers_id),
        signatures=[venue.get_id()],
        note=Note(content=config),
    )
    assert config_note

    response = test_client.post(
        "/match",
        data=json.dumps({"configNoteId": config_note["note"]["id"]}),
        content_type="application/json",
        headers=openreview_client.headers,
    )
    assert response.status_code == 200

    matcher_status = wait_for_status(
        openreview_client, config_note["note"]["id"], api_version=2
    )

    config_note = openreview_client.get_note(config_note["note"]["id"])
    assert matcher_status.content["status"]["value"] == "Complete"

    paper_assignment_edges = openreview_client.get_edges_count(
        label="integration-test",
        invitation=venue.get_assignment_id(venue.get_reviewers_id()),
    )

    assert paper_assignment_edges == num_papers * reviews_per_paper


def test_routes_invalid_invitation(
    openreview_context, celery_app, celery_session_worker
):
    """"""
    openreview_client = openreview_context["openreview_client_v2"]
    test_client = openreview_context["test_client"]

    conference_id = "ICLS.cc/2022/Conference"
    num_reviewers = 10
    num_papers = 10
    reviews_per_paper = 3
    max_papers = 5
    min_papers = 1
    alternates = 0

    venue = clean_start_conference_v2(
        openreview_client,
        conference_id,
        num_reviewers,
        num_papers,
        reviews_per_paper,
    )

    reviewers_id = venue.get_reviewers_id()

    config = {
        "title": {"value": "integration-test"},
        "user_demand": {"value": str(reviews_per_paper)},
        "max_papers": {"value": str(max_papers)},
        "min_papers": {"value": str(min_papers)},
        "alternates": {"value": str(alternates)},
        "config_invitation": {
            "value": "{}/-/Assignment_Configuration".format(reviewers_id)
        },
        "paper_invitation": {"value": venue.get_submission_id()},
        "assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id)
        },
        "deployed_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, deployed=True)
        },
        "invite_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, invite=True)
        },
        "aggregate_score_invitation": {
            "value": "{}/-/Aggregate_Score".format(reviewers_id)
        },
        "conflicts_invitation": {
            "value": venue.get_conflict_score_id(reviewers_id)
        },
        "custom_max_papers_invitation": {
            "value": "{}/-/Custom_Max_Papers".format(reviewers_id)
        },
        "match_group": {"value": reviewers_id},
        "scores_specification": {
            "value": {
                # conference.get_affinity_score_id(reviewers_id): {
                #     'weight': 1.0,
                #     'default': 0.0
                # },
                "<some_invalid_invitation>": {"weight": 1.0, "default": 0.0}
            }
        },
        "status": {"value": "Initialized"},
        "solver": {"value": "MinMax"},
    }

    config_note = openreview_client.post_note_edit(
        invitation="{}/-/Assignment_Configuration".format(reviewers_id),
        signatures=[venue.get_id()],
        note=Note(content=config),
    )
    assert config_note

    invalid_invitation_response = test_client.post(
        "/match",
        data=json.dumps({"configNoteId": config_note["note"]["id"]}),
        content_type="application/json",
        headers=openreview_client.headers,
    )
    assert invalid_invitation_response.status_code == 404

    config_note = openreview_client.get_note(config_note["note"]["id"])
    assert config_note.content["status"]["value"] == "Error"


def test_routes_missing_header(openreview_context, celery_app, celery_session_worker):
    """request with missing header should response with 400"""
    openreview_client = openreview_context["openreview_client_v2"]
    test_client = openreview_context["test_client"]

    conference_id = "ICLS.cc/2023/Conference"
    num_reviewers = 10
    num_papers = 10
    reviews_per_paper = 3
    max_papers = 5
    min_papers = 1
    alternates = 0

    venue = clean_start_conference_v2(
        openreview_client,
        conference_id,
        num_reviewers,
        num_papers,
        reviews_per_paper,
    )

    reviewers_id = venue.get_reviewers_id()

    config = {
        "title": {"value": "integration-test"},
        "user_demand": {"value": str(reviews_per_paper)},
        "max_papers": {"value": str(max_papers)},
        "min_papers": {"value": str(min_papers)},
        "alternates": {"value": str(alternates)},
        "config_invitation": {
            "value": "{}/-/Assignment_Configuration".format(reviewers_id)
        },
        "paper_invitation": {"value": venue.get_submission_id()},
        "assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id)
        },
        "deployed_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, deployed=True)
        },
        "invite_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, invite=True)
        },
        "aggregate_score_invitation": {
            "value": "{}/-/Aggregate_Score".format(reviewers_id)
        },
        "conflicts_invitation": {
            "value": venue.get_conflict_score_id(reviewers_id)
        },
        "custom_max_papers_invitation": {
            "value": "{}/-/Custom_Max_Papers".format(reviewers_id)
        },
        "match_group": {"value": reviewers_id},
        "scores_specification": {
            "value": {
                venue.get_affinity_score_id(reviewers_id): {
                    "weight": 1.0,
                    "default": 0.0,
                }
            }
        },
        "status": {"value": "Initialized"},
        "solver": {"value": "MinMax"},
    }

    config_note = openreview_client.post_note_edit(
        invitation="{}/-/Assignment_Configuration".format(reviewers_id),
        signatures=[venue.get_id()],
        note=Note(content=config),
    )
    assert config_note

    missing_header_response = test_client.post(
        "/match",
        data=json.dumps({"configNoteId": config_note["note"]["id"]}),
        content_type="application/json",
    )
    assert missing_header_response.status_code == 400


def test_routes_missing_config(openreview_context, celery_app, celery_session_worker):
    """should return 404 if config note doesn't exist"""

    openreview_client = openreview_context["openreview_client_v2"]
    test_client = openreview_context["test_client"]

    missing_config_response = test_client.post(
        "/match",
        data=json.dumps({"configNoteId": "BAD_CONFIG_NOTE_ID"}),
        content_type="application/json",
        headers=openreview_client.headers,
    )
    assert missing_config_response.status_code == 404


@pytest.mark.skip  # TODO: fix the authorization so that this test passes.
def test_routes_bad_token(openreview_context, celery_app, celery_session_worker):
    """should return 400 if token is bad"""
    openreview_client = openreview_context["openreview_client"]
    test_client = openreview_context["test_client"]
    app = openreview_context["app"]

    bad_token_response = test_client.post(
        "/match",
        data=json.dumps({"configNoteId": "BAD_CONFIG_NOTE_ID"}),
        content_type="application/json",
        headers={"Authorization": "BAD_TOKEN"},
    )
    assert bad_token_response.status_code == 400


def test_routes_already_running_or_complete(
    openreview_context, celery_app, celery_session_worker
):
    """should return 400 if the match is already running or complete"""

    openreview_client = openreview_context["openreview_client_v2"]
    test_client = openreview_context["test_client"]

    conference_id = "ICLS.cc/2024/Conference"
    num_reviewers = 1
    num_papers = 1
    reviews_per_paper = 1
    max_papers = 1
    min_papers = 0
    alternates = 0

    venue = clean_start_conference_v2(
        openreview_client,
        conference_id,
        num_reviewers,
        num_papers,
        reviews_per_paper,
    )

    reviewers_id = venue.get_reviewers_id()

    config = {
        "title": {"value": "integration-test"},
        "user_demand": {"value": str(reviews_per_paper)},
        "max_papers": {"value": str(max_papers)},
        "min_papers": {"value": str(min_papers)},
        "alternates": {"value": str(alternates)},
        "config_invitation": {
            "value": "{}/-/Assignment_Configuration".format(reviewers_id)
        },
        "paper_invitation": {"value": venue.get_submission_id()},
        "assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id)
        },
        "deployed_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, deployed=True)
        },
        "invite_assignment_invitation": {
            "value": venue.get_assignment_id(reviewers_id, invite=True)
        },
        "aggregate_score_invitation": {
            "value": "{}/-/Aggregate_Score".format(reviewers_id)
        },
        "conflicts_invitation": {
            "value": venue.get_conflict_score_id(reviewers_id)
        },
        "custom_max_papers_invitation": {
            "value": "{}/-/Custom_Max_Papers".format(reviewers_id)
        },
        "match_group": {"value": reviewers_id},
        "scores_specification": {
            "value": {
                venue.get_affinity_score_id(reviewers_id): {
                    "weight": 1.0,
                    "default": 0.0,
                }
            }
        },
        "status": {"value": "Running"},
        "solver": {"value": "MinMax"},
    }

    config_note = openreview_client.post_note_edit(
        invitation="{}/-/Assignment_Configuration".format(reviewers_id),
        signatures=[venue.get_id()],
        note=Note(content=config),
    )
    assert config_note

    already_running_response = test_client.post(
        "/match",
        data=json.dumps({"configNoteId": config_note["note"]["id"]}),
        content_type="application/json",
        headers=openreview_client.headers,
    )
    assert already_running_response.status_code == 400

    config_note = openreview_client.get_note(config_note["note"]["id"])
    assert config_note.content["status"]["value"] == "Running"

    config_note.content["status"]["value"] = "Complete"
    config_note = openreview_client.post_note_edit(
        invitation="{}/-/Assignment_Configuration".format(reviewers_id),
        signatures=[venue.get_id()],
        note=Note(id=config_note.id, content=config_note.content),
    )
    assert config_note
    print(
        "config note set to: ",
        config_note["note"]["content"]["status"]["value"],
    )

    already_complete_response = test_client.post(
        "/match",
        data=json.dumps({"configNoteId": config_note["note"]["id"]}),
        content_type="application/json",
        headers=openreview_client.headers,
    )
    assert already_complete_response.status_code == 400
    config_note = openreview_client.get_note(config_note["note"]["id"])
    assert config_note.content["status"]["value"] == "Complete"
