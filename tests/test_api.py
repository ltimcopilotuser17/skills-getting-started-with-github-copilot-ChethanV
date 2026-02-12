"""
Test suite for Mergington High School API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original data
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
    }
    
    # Reset to original state
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activity_structure(self, client):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_activity_not_found(self, client):
        """Test signup for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_registration(self, client):
        """Test that duplicate registrations are prevented"""
        email = "duplicate@mergington.edu"
        activity = "Chess Club"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with special characters in email"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test.user+tag@mergington.edu"
        )
        assert response.status_code == 200


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participant/{email} endpoint"""
    
    def test_remove_participant_successful(self, client):
        """Test successful removal of a participant"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Verify participant exists
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]
        
        # Remove participant
        response = client.delete(
            f"/activities/{activity.replace(' ', '%20')}/participant/{email}"
        )
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]
    
    def test_remove_participant_activity_not_found(self, client):
        """Test removing participant from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/participant/test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_remove_participant_not_registered(self, client):
        """Test removing a participant that isn't registered"""
        response = client.delete(
            "/activities/Chess%20Club/participant/notregistered@mergington.edu"
        )
        assert response.status_code == 404
        assert "not registered" in response.json()["detail"]
    
    def test_remove_and_re_add_participant(self, client):
        """Test removing and re-adding a participant"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Remove participant
        response1 = client.delete(
            f"/activities/{activity.replace(' ', '%20')}/participant/{email}"
        )
        assert response1.status_code == 200
        
        # Re-add participant
        response2 = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify participant is back
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]


class TestIntegrationScenarios:
    """Integration tests for common user scenarios"""
    
    def test_full_signup_workflow(self, client):
        """Test complete signup workflow"""
        email = "integration@mergington.edu"
        activity = "Programming Class"
        
        # Get initial participant count
        initial = client.get("/activities").json()[activity]["participants"]
        initial_count = len(initial)
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify participant count increased
        after_signup = client.get("/activities").json()[activity]["participants"]
        assert len(after_signup) == initial_count + 1
        assert email in after_signup
        
        # Try to sign up again (should fail)
        duplicate_response = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
        )
        assert duplicate_response.status_code == 400
        
        # Remove participant
        remove_response = client.delete(
            f"/activities/{activity.replace(' ', '%20')}/participant/{email}"
        )
        assert remove_response.status_code == 200
        
        # Verify participant count decreased
        after_removal = client.get("/activities").json()[activity]["participants"]
        assert len(after_removal) == initial_count
        assert email not in after_removal
    
    def test_multiple_signups_different_activities(self, client):
        """Test a student signing up for multiple activities"""
        email = "multisport@mergington.edu"
        
        # Sign up for multiple activities
        activities_to_join = ["Chess Club", "Programming Class", "Gym Class"]
        
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify student is in all activities
        all_activities = client.get("/activities").json()
        for activity in activities_to_join:
            assert email in all_activities[activity]["participants"]
