from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from store.models import Metadata, ChangeReason, RelationshipTypes, Relationships
from unittest.mock import patch, MagicMock
import json

User = get_user_model()


class AuthenticatedViewTest(TestCase):
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
    def test_home_view_requires_login(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)

    def test_home_view_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertInHTML("Search Metadata Store", response.text)


class ResultsViewTest(AuthenticatedViewTest):
    def setUp(self):
        super().setUp()
        Metadata.objects.create(
            id="meta-002",
            type="document",
            catalogue_reference="REF-002",
            metadata={"title": "Another Document"},
        )

    def test_results_view_requires_login(self):
        response = self.client.get("/results?q=test")
        self.assertEqual(response.status_code, 302)

    def test_results_view_authenticated_no_query(self):
        self.client.force_login(self.user)
        response = self.client.get("/results?q=")
        self.assertEqual(response.status_code, 200)
        self.assertInHTML("REF-002", response.text)
        self.assertInHTML("REF-001", response.text)

    def test_results_view_authenticated_with_query(self):
        self.client.force_login(self.user)
        response = self.client.get("/results?q=REF-001")
        self.assertEqual(response.status_code, 200)
        self.assertNotInHTML("REF-002", response.text)
        self.assertInHTML("REF-001", response.text)

    def test_results_view_case_insensitive(self):
        self.client.force_login(self.user)
        response = self.client.get("/results?q=ref-001")
        self.assertEqual(response.status_code, 200)
        self.assertNotInHTML("REF-002", response.text)
        self.assertInHTML("REF-001", response.text)


class UploadViewTest(AuthenticatedViewTest):
    def test_upload_view_get_requires_login(self):
        response = self.client.get(f"/upload/{self.metadata.id}")
        self.assertEqual(response.status_code, 302)

    def test_upload_view_get_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(f"/upload/{self.metadata.id}")
        self.assertEqual(response.status_code, 200)
        self.assertInHTML("Upload json file", response.text)

    def test_upload_view_post_requires_login(self):
        response = self.client.post(f"/upload/{self.metadata.id}")
        self.assertEqual(response.status_code, 302)

    def test_upload_view_post_invalid_form(self):
        self.client.force_login(self.user)
        response = self.client.post(
            f"/upload/{self.metadata.id}",
            {},  # Missing file and reason
        )
        self.assertEqual(response.status_code, 200)
        self.assertInHTML("A reason is required", response.text)
        self.assertInHTML("A json file is required", response.text)


class SubmittedViewTest(AuthenticatedViewTest):
    def test_submitted_view_requires_login(self):
        response = self.client.get(f"/submitted/{self.metadata.id}")
        self.assertEqual(response.status_code, 302)

    def test_submitted_view_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(f"/submitted/{self.metadata.id}")
        self.assertEqual(response.status_code, 200)


class RecordsViewTest(AuthenticatedViewTest):
    def setUp(self):
        super().setUp()
        self.metadata2 = Metadata.objects.create(
            id="meta-002",
            type="document",
            catalogue_reference="REF-002",
            metadata={"title": "Related Document"},
        )

    def test_records_view_requires_login(self):
        response = self.client.get(f"/records/{self.metadata.id}")
        self.assertEqual(response.status_code, 302)

    def test_records_view_renders_metadata(self):
        self.client.force_login(self.user)
        response = self.client.get(f"/records/{self.metadata.id}")
        self.assertEqual(response.status_code, 200)

    def test_records_view_with_relationships(self):
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
        response = self.client.get("/records/nonexistent-id")
        self.assertEqual(response.status_code, 302)


class ApiRecordViewTest(TestCase):
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
        response = self.client.get(f"/api/records/meta-001")
        self.assertEqual(response.status_code, 401)

    def test_api_record_auth_required_before_checking_existence(self):
        response = self.client.get("/api/records/nonexistent")
        self.assertEqual(response.status_code, 401)

    def test_api_record_with_bearer_token_invalid_token(self):
        response = self.client.get(
            f"/api/records/meta-001", HTTP_AUTHORIZATION="Bearer invalid-token-123"
        )
        self.assertEqual(response.status_code, 401)

    def test_api_record_with_malformed_bearer_header(self):
        response = self.client.get(
            f"/api/records/meta-001", HTTP_AUTHORIZATION="NotBearerToken something"
        )
        self.assertEqual(response.status_code, 401)

    @patch("store.views.require_auth.acquire_token")
    def test_api_record_with_valid_token_returns_metadata(self, mock_acquire):
        mock_acquire.return_value = MagicMock()
        response = self.client.get(
            f"/api/records/meta-001", HTTP_AUTHORIZATION="Bearer valid-token-123"
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn("metadata", response_data)
        self.assertIn("audit", response_data)
        self.assertEqual(response_data["metadata"]["title"], "Test Document")
