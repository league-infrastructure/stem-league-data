"""Unit tests for API health and basic endpoints."""

import pytest


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_returns_200(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_returns_healthy_status(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_returns_200(self, client):
        """Root endpoint should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_returns_welcome_message(self, client):
        """Root endpoint should return welcome message."""
        response = client.get("/")
        data = response.json()
        assert "message" in data
        assert "STEM League" in data["message"]


class TestAdminStats:
    """Tests for admin stats endpoint."""
    
    def test_stats_returns_200(self, client):
        """Stats endpoint should return 200 OK."""
        response = client.get("/api/admin/stats")
        assert response.status_code == 200
    
    def test_stats_returns_counts(self, client):
        """Stats endpoint should return record counts."""
        response = client.get("/api/admin/stats")
        data = response.json()
        
        # Should have counts for all model types
        assert "orgs" in data
        assert "venues" in data
        assert "persons" in data
        assert "total" in data
        
        # Counts should be integers
        assert isinstance(data["orgs"], int)
        assert isinstance(data["total"], int)
    
    def test_stats_empty_database(self, client):
        """Stats should show zero counts for empty database."""
        response = client.get("/api/admin/stats")
        data = response.json()
        
        # Fresh database should have zero records
        assert data["total"] == 0
        assert data["orgs"] == 0


class TestAdminResetDatabase:
    """Tests for admin reset database endpoint."""
    
    def test_reset_database_returns_200(self, client):
        """Reset database endpoint should return 200 OK."""
        response = client.post("/api/admin/reset-database")
        assert response.status_code == 200
    
    def test_reset_database_returns_success(self, client):
        """Reset database endpoint should return success message."""
        response = client.post("/api/admin/reset-database")
        data = response.json()
        assert data["status"] == "success"
