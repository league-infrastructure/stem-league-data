"""Unit tests for Places API endpoints (metros, orgs, venues, flyers)."""

import pytest


class TestMetrosAPI:
    """Tests for metros endpoints."""
    
    def test_list_metros_empty(self, client):
        """List metros should return empty list for fresh database."""
        response = client.get("/api/metros")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_metros_with_data(self, seeded_client):
        """List metros should return metros from database."""
        response = seeded_client.get("/api/metros")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Metro"
    
    def test_get_metro_not_found(self, client):
        """Get metro with invalid ID should return 404."""
        response = client.get("/api/metros/999")
        assert response.status_code == 404
    
    def test_get_metro_by_id(self, seeded_client):
        """Get metro by ID should return the metro."""
        response = seeded_client.get("/api/metros/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Metro"
    
    def test_create_metro(self, client):
        """Create metro should return 201 with created metro."""
        metro_data = {"name": "New Metro", "slug": "new-metro"}
        response = client.post("/api/metros", json=metro_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Metro"
        assert data["slug"] == "new-metro"
        assert "id" in data
    
    def test_update_metro(self, seeded_client):
        """Update metro should return updated metro."""
        update_data = {"name": "Updated Metro"}
        response = seeded_client.put("/api/metros/1", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Metro"
    
    def test_delete_metro(self, test_db, client):
        """Delete metro should return 204."""
        from stem_league_data.models import Metro
        
        # Create a metro to delete (no foreign key dependencies)
        with test_db.session_scope() as session:
            metro = Metro(name="To Delete", slug="to-delete")
            session.add(metro)
            session.flush()
            metro_id = metro.id
        
        response = client.delete(f"/api/metros/{metro_id}")
        assert response.status_code == 204
        
        # Verify it's deleted
        response = client.get(f"/api/metros/{metro_id}")
        assert response.status_code == 404
    
    def test_count_metros(self, seeded_client):
        """Count metros should return count."""
        response = seeded_client.get("/api/metros/count")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1


class TestOrgsAPI:
    """Tests for orgs endpoints."""
    
    def test_list_orgs_empty(self, client):
        """List orgs should return empty list for fresh database."""
        response = client.get("/api/orgs")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_orgs_with_data(self, seeded_client):
        """List orgs should return orgs from database."""
        response = seeded_client.get("/api/orgs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Organization"
    
    def test_create_org(self, seeded_client):
        """Create org should return 201 with created org."""
        org_data = {
            "name": "New Org",
            "metro_id": 1,
        }
        response = seeded_client.post("/api/orgs", json=org_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Org"
    
    def test_get_org_by_id(self, seeded_client):
        """Get org by ID should return the org."""
        response = seeded_client.get("/api/orgs/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Organization"


class TestVenuesAPI:
    """Tests for venues endpoints."""
    
    def test_list_venues_empty(self, client):
        """List venues should return empty list for fresh database."""
        response = client.get("/api/venues")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_venues_with_data(self, seeded_client):
        """List venues should return venues from database."""
        response = seeded_client.get("/api/venues")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Venue"
    
    def test_create_venue(self, seeded_client):
        """Create venue should return 201 with created venue."""
        venue_data = {
            "name": "New Venue",
            "address": "456 New St",
            "metro_id": 1,
            "org_id": 1,
        }
        response = seeded_client.post("/api/venues", json=venue_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Venue"
    
    def test_list_venues_pagination(self, seeded_client):
        """List venues should support pagination."""
        response = seeded_client.get("/api/venues?skip=0&limit=10")
        assert response.status_code == 200


class TestFlyersAPI:
    """Tests for flyers endpoints."""
    
    def test_list_flyers_empty(self, client):
        """List flyers should return empty list for fresh database."""
        response = client.get("/api/flyers")
        assert response.status_code == 200
        assert response.json() == []
