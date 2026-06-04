from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from store.models import Metadata, ChangeReason, RelationshipTypes, Relationships
from unittest.mock import patch, MagicMock
import json

User = get_user_model()

User = get_user_model()


class AuthenticatedViewTest(TestCase):
    """Base class for authenticated view tests with common setup"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )
        self.metadata = Metadata.objects.create(
            id="meta-001",
            type="document",
            catalogue_reference="REF-001",
            metadata={"title": "Test Document"},
        )
        ChangeReason.objects.create(id="reason-001", reason="Test reason")


class HomeViewTest(AuthenticatedViewTest):
    """Test the home view"""

    def test_home_view_requires_login(self):
        """Test that home view redirects to login when not authenticated"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)

    def test_home_view_authenticated(self):
        """Test home view when authenticated"""
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


class ResultsViewTest(AuthenticatedViewTest):
    """Test the results/search view"""

    def setUp(self):
        super().setUp()
        # Create additional test data
        Metadata.objects.create(
            id="meta-002",
            type="document",
            catalogue_reference="REF-002",
            metadata={"title": "Another Document"},
        )

    def test_results_view_requires_login(self):
        """Test that results view requires login"""
        response = self.client.get("/results?q=test")
        self.assertEqual(response.status_code, 302)

    def test_results_view_authenticated_no_query(self):
        """Test results view with no search query returns all records"""
        self.client.force_login(self.user)
        response = self.client.get("/results?q=")
        self.assertEqual(response.status_code, 200)

    def test_results_view_authenticated_with_query(self):
        """Test results view with search query filters by catalogue_reference"""
        self.client.force_login(self.user)
        response = self.client.get("/results?q=REF-001")
        self.assertEqual(response.status_code, 200)

    def test_results_view_case_insensitive(self):
        """Test that search is case insensitive"""
        self.client.force_login(self.user)
        response = self.client.get("/results?q=ref-001")
        self.assertEqual(response.status_code, 200)


class UploadViewTest(AuthenticatedViewTest):
    """Test the upload view"""

    def test_upload_view_get_requires_login(self):
        """Test that GET to upload requires login"""
        response = self.client.get(f"/upload/{self.metadata.id}")
        self.assertEqual(response.status_code, 302)

    def test_upload_view_get_authenticated(self):
        """Test GET upload view when authenticated"""
        self.client.force_login(self.user)
        response = self.client.get(f"/upload/{self.metadata.id}")
        self.assertEqual(response.status_code, 200)

    def test_upload_view_post_requires_login(self):
        """Test that POST to upload requires login"""
        response = self.client.post(f"/upload/{self.metadata.id}")
        self.assertEqual(response.status_code, 302)

    def test_upload_view_post_invalid_form(self):
        """Test upload POST with invalid form (missing required fields)"""
        self.client.force_login(self.user)
        response = self.client.post(
            f"/upload/{self.metadata.id}",
            {},  # Missing file and reason
        )
        self.assertEqual(response.status_code, 200)


class SubmittedViewTest(AuthenticatedViewTest):
    """Test the submitted view"""

    def test_submitted_view_requires_login(self):
        """Test that submitted view requires login"""
        response = self.client.get(f"/submitted/{self.metadata.id}")
        self.assertEqual(response.status_code, 302)

    def test_submitted_view_authenticated(self):
        """Test submitted view when authenticated"""
        self.client.force_login(self.user)
        response = self.client.get(f"/submitted/{self.metadata.id}")
        self.assertEqual(response.status_code, 200)


class RecordsViewTest(AuthenticatedViewTest):
    """Test the records/detail view"""

    def setUp(self):
        super().setUp()
        self.metadata2 = Metadata.objects.create(
            id="meta-002",
            type="document",
            catalogue_reference="REF-002",
            metadata={"title": "Related Document"},
        )

    def test_records_view_requires_login(self):
        """Test that records view requires login"""
        response = self.client.get(f"/records/{self.metadata.id}")
        self.assertEqual(response.status_code, 302)

    def test_records_view_renders_metadata(self):
        """Test that records view renders metadata when authenticated"""
        self.client.force_login(self.user)
        response = self.client.get(f"/records/{self.metadata.id}")
        self.assertEqual(response.status_code, 200)

    def test_records_view_with_relationships(self):
        """Test that records view shows relationships"""
        self.client.force_login(self.user)
        rel_type = RelationshipTypes.objects.create(
            type="related_to",
            to_label="related",
            from_label="related_from",
        )
        Relationships.objects.create(
            from_asset=self.metadata,
            to_asset=self.metadata2,
            type=rel_type,
        )

        response = self.client.get(f"/records/{self.metadata.id}")
        self.assertEqual(response.status_code, 200)

    def test_records_view_nonexistent_redirects_to_login(self):
        """Test records view with nonexistent ID redirects to login when not authenticated"""
        response = self.client.get("/records/nonexistent-id")
        self.assertEqual(response.status_code, 302)


class ApiRecordViewTest(TestCase):
    """Test the API endpoint for record data"""

    def setUp(self):
        self.client = Client()
        self.metadata = Metadata.objects.create(
            id="meta-001",
            type="document",
            catalogue_reference="REF-001",
            metadata={"title": "Test Document"},
        )
        ChangeReason.objects.create(id="reason-001", reason="Test change")

    def test_api_record_requires_auth_returns_401(self):
        """Test that API endpoint requires authentication"""
        response = self.client.get(f"/api/records/meta-001")
        # Without auth, should return 401 (Unauthorized)
        self.assertEqual(response.status_code, 401)

    def test_api_record_auth_required_before_checking_existence(self):
        """Test that API requires auth before checking record existence"""
        response = self.client.get("/api/records/nonexistent")
        # Should check auth first, return 401 even for non-existent record
        self.assertEqual(response.status_code, 401)

    def test_api_record_with_bearer_token_invalid_token(self):
        """Test API endpoint with invalid Bearer token"""
        response = self.client.get(
            f"/api/records/meta-001", HTTP_AUTHORIZATION="Bearer invalid-token-123"
        )
        # Invalid JWT token should still return 401
        self.assertEqual(response.status_code, 401)

    def test_api_record_with_malformed_bearer_header(self):
        """Test API endpoint with malformed auth header"""
        response = self.client.get(
            f"/api/records/meta-001", HTTP_AUTHORIZATION="NotBearerToken something"
        )
        # Malformed header should return 401
        self.assertEqual(response.status_code, 401)
