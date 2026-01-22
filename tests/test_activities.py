import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities before each test"""
    # Store original state
    original_activities = {
        key: {
            "description": value["description"],
            "schedule": value["schedule"],
            "max_participants": value["max_participants"],
            "participants": value["participants"].copy(),
        }
        for key, value in activities.items()
    }
    
    yield
    
    # Restore original state
    for key, value in original_activities.items():
        activities[key]["participants"] = value["participants"]


class TestGetActivities:
    def test_get_activities_returns_200(self):
        """Test that GET /activities returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_has_expected_fields(self):
        """Test that activities have expected fields"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_details in activities_data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignup:
    def test_signup_new_student(self):
        """Test signing up a new student"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        assert "test@mergington.edu" in response.json()["message"]

    def test_signup_duplicate_student_fails(self):
        """Test that signing up the same student twice fails"""
        # First signup
        client.post("/activities/Chess Club/signup?email=duplicate@mergington.edu")
        
        # Second signup with same email should fail
        response = client.post(
            "/activities/Chess Club/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_nonexistent_activity_fails(self):
        """Test signing up for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_adds_participant_to_list(self):
        """Test that signup actually adds participant to the activity"""
        email = "newstudent@mergington.edu"
        activity_name = "Swimming Club"
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify participant is in the list
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        assert email in participants


class TestUnregister:
    def test_unregister_existing_participant(self):
        """Test unregistering an existing participant"""
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # Verify they're signed up initially
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes participant from list"""
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # Unregister
        client.post(f"/activities/{activity_name}/unregister?email={email}")
        
        # Verify participant is removed
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        assert email not in participants

    def test_unregister_nonexistent_participant_fails(self):
        """Test unregistering a participant not in activity"""
        response = client.post(
            "/activities/Art Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_nonexistent_activity_fails(self):
        """Test unregistering from non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestRootRedirect:
    def test_root_redirects_to_static(self):
        """Test that root path redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [301, 302, 307, 308]
        assert "/static/index.html" in response.headers.get("location", "")
