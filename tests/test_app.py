from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


ACTIVITY = "Art Club"
EXISTING_ACTIVITY = "Chess Club"


@pytest.fixture
def isolated_activities(monkeypatch):
    activity_data = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", activity_data)
    return activity_data


@pytest.fixture
def client(isolated_activities):
    return TestClient(app_module.app)


def test_root_redirects_to_activity_page(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client, isolated_activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == isolated_activities


def test_signup_adds_participant(client, isolated_activities):
    email = "new-student@mergington.edu"
    activity_path = quote(ACTIVITY, safe="")

    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {ACTIVITY}"}
    assert email in isolated_activities[ACTIVITY]["participants"]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant(client):
    email = "michael@mergington.edu"
    activity_path = quote(EXISTING_ACTIVITY, safe="")

    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_signup_requires_email(client):
    activity_path = quote(ACTIVITY, safe="")

    response = client.post(f"/activities/{activity_path}/signup")

    assert response.status_code == 422


def test_unregister_removes_participant(client, isolated_activities):
    email = "michael@mergington.edu"
    activity_path = quote(EXISTING_ACTIVITY, safe="")

    response = client.delete(
        f"/activities/{activity_path}/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {EXISTING_ACTIVITY}"
    }
    assert email not in isolated_activities[EXISTING_ACTIVITY]["participants"]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Activity/participants",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_nonparticipant(client):
    activity_path = quote(EXISTING_ACTIVITY, safe="")

    response = client.delete(
        f"/activities/{activity_path}/participants",
        params={"email": "not-signed-up@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_requires_email(client):
    activity_path = quote(EXISTING_ACTIVITY, safe="")

    response = client.delete(f"/activities/{activity_path}/participants")

    assert response.status_code == 422