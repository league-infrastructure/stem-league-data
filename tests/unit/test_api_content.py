"""Unit tests for Content API endpoints."""

import pytest


class TestContentsAPI:
    """Tests for contents endpoints."""
    
    def test_list_contents_empty(self, client):
        """List contents should return empty list for fresh database."""
        response = client.get("/api/contents")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_contents_with_data(self, seeded_client):
        """List contents should return contents from database."""
        response = seeded_client.get("/api/contents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Content"
    
    def test_get_content_not_found(self, client):
        """Get content with invalid ID should return 404."""
        response = client.get("/api/contents/999")
        assert response.status_code == 404
    
    def test_get_content_by_id(self, seeded_client):
        """Get content by ID should return the content."""
        response = seeded_client.get("/api/contents/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Test Content"
    
    def test_create_content(self, client):
        """Create content should return 201 with created content."""
        content_data = {
            "title": "New Content",
            "blurb": "A new content item",
            "description": "Full description here",
        }
        response = client.post("/api/contents", json=content_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Content"
        assert data["blurb"] == "A new content item"
        assert "id" in data
        assert "content_type" in data
    
    def test_update_content(self, seeded_client):
        """Update content should return updated content."""
        update_data = {"title": "Updated Title", "blurb": "Updated blurb"}
        response = seeded_client.put("/api/contents/1", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["blurb"] == "Updated blurb"
    
    def test_delete_content(self, test_db, client):
        """Delete content should return 204."""
        from stem_league_data.models import Content
        
        # Create a content to delete
        with test_db.session_scope() as session:
            content = Content(
                title="To Delete",
                content_type="content",
            )
            session.add(content)
            session.flush()
            content_id = content.id
        
        response = client.delete(f"/api/contents/{content_id}")
        assert response.status_code == 204
        
        # Verify it's deleted
        response = client.get(f"/api/contents/{content_id}")
        assert response.status_code == 404
    
    def test_count_contents(self, seeded_client):
        """Count contents should return count."""
        response = seeded_client.get("/api/contents/count")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
    
    def test_content_pagination(self, client):
        """Contents endpoint should support pagination."""
        response = client.get("/api/contents?skip=0&limit=10")
        assert response.status_code == 200
    
    def test_content_with_all_fields(self, client):
        """Create content with all optional fields."""
        content_data = {
            "title": "Full Content",
            "eyebrow": "Category",
            "label": "Label",
            "blurb": "Short description",
            "description": "Long description",
            "body": "Full body content",
            "instructions": "Some instructions",
            "image": "https://example.com/image.jpg",
            "link": "https://example.com",
            "source": "manual",
            "for_": "students",
            "rank": 10,
            "renderer": "default",
            "comment": "Internal comment",
            "type": "article",
        }
        response = client.post("/api/contents", json=content_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Full Content"
        assert data["for_"] == "students"
        assert data["rank"] == 10


class TestAnnouncementsAPI:
    """Tests for announcements endpoints."""
    
    def test_list_announcements_empty(self, client):
        """List announcements should return empty list for fresh database."""
        response = client.get("/api/announcements")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_announcement(self, seeded_client):
        """Create announcement should return 201."""
        announcement_data = {
            "content_id": 1,
            "from_date": "2026-01-01T00:00:00",
            "until_date": "2026-12-31T23:59:59",
        }
        response = seeded_client.post("/api/announcements", json=announcement_data)
        assert response.status_code == 201
        data = response.json()
        assert data["content_id"] == 1
