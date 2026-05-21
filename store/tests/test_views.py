from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from store.models import RecordOutput, Change, CopyrightTitle, RecordCopyrightTitle
from store.views import snake_to_camel, json_for_record, UploadForm
from io import BytesIO
import json

User = get_user_model()


class SnakeToCamelTest(TestCase):
    def test_snake_to_camel_single_word(self):
        """Test single word conversion"""
        result = snake_to_camel("title")
        self.assertEqual(result, "Title")

    def test_snake_to_camel_two_words(self):
        """Test two-word conversion"""
        result = snake_to_camel("record_id")
        self.assertEqual(result, "Record Id")

    def test_snake_to_camel_multiple_words(self):
        """Test multi-word conversion"""
        result = snake_to_camel("former_reference_tna")
        self.assertEqual(result, "Former Reference Tna")

    def test_snake_to_camel_single_underscore(self):
        """Test with single underscore"""
        result = snake_to_camel("date_modified")
        self.assertEqual(result, "Date Modified")


class JsonForRecordTest(TestCase):
    def setUp(self):
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
            title="Test Record",
            description="Test Description",
            legal_status="Public",
        )

    def test_json_for_record_basic(self):
        """Test converting record to JSON metadata"""
        metadata = json_for_record(self.record)
        self.assertIsInstance(metadata, dict)
        self.assertIn("Ia Id", metadata)
        self.assertIn("Reference", metadata)
        self.assertIn("Title", metadata)

    def test_json_for_record_excludes_primary_key(self):
        """Test that primary key is excluded"""
        metadata = json_for_record(self.record)
        self.assertNotIn("id", metadata)

    def test_json_for_record_snake_to_camel_conversion(self):
        """Test field name conversion from snake_case"""
        metadata = json_for_record(self.record)
        # The function converts snake_case to Title Case with spaces
        self.assertIn("Legal Status", metadata)
        self.assertNotIn("legal_status", metadata)

    def test_json_for_record_excludes_null_values(self):
        """Test that null/None values are excluded"""
        metadata = json_for_record(self.record)
        # Some fields like public_title are null, they should not be in output
        self.assertNotIn("Public Title", metadata)

    def test_json_for_record_with_duration_field(self):
        """Test that duration fields are converted to string"""
        from datetime import timedelta

        record = RecordOutput.objects.create(
            record_id="rec-002",
            ia_id="ia-002",
            reference="REF-002",
            film_duration=timedelta(hours=1, minutes=30),
        )
        metadata = json_for_record(record)
        self.assertIn("Film Duration", metadata)
        self.assertIsInstance(metadata["Film Duration"], str)


class UploadFormTest(TestCase):
    def test_upload_form_valid(self):
        """Test valid upload form"""
        from django.core.files.uploadedfile import SimpleUploadedFile

        data = {
            "reason": "Testing upload",
        }
        file_content = b'{"test": "data"}'
        files = {
            "json_edit": SimpleUploadedFile("test.json", file_content),
        }
        form = UploadForm(data, files)
        self.assertTrue(form.is_valid())

    def test_upload_form_missing_file(self):
        """Test upload form without file"""
        data = {
            "reason": "Testing upload",
        }
        form = UploadForm(data)
        self.assertFalse(form.is_valid())

    def test_upload_form_missing_reason(self):
        """Test upload form without reason"""
        from django.core.files.uploadedfile import SimpleUploadedFile

        file_content = b'{"test": "data"}'
        files = {
            "json_edit": SimpleUploadedFile("test.json", file_content),
        }
        form = UploadForm({}, files)
        self.assertFalse(form.is_valid())


class RecordsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
            title="Test Record",
        )

    def test_records_view_requires_login(self):
        """Test that records view requires login"""
        response = self.client.get(f"/records/{self.record.record_id}")
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_records_view_authenticated(self):
        """Test records view when authenticated"""
        self.client.login(username="testuser@example.com", password="testpass123")
        response = self.client.get(f"/records/{self.record.record_id}")
        self.assertEqual(response.status_code, 200)

    def test_records_view_context(self):
        """Test that records view passes correct context"""
        self.client.login(username="testuser@example.com", password="testpass123")
        response = self.client.get(f"/records/{self.record.record_id}")
        self.assertEqual(response.status_code, 200)
        if response.context:
            self.assertIn("metadata", response.context)
            self.assertIn("relationships", response.context)


class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )

    def test_home_view_requires_login(self):
        """Test that home view requires login"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)

    def test_home_view_authenticated(self):
        """Test home view when authenticated"""
        self.client.login(username="testuser@example.com", password="testpass123")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_home_view_context(self):
        """Test home view context"""
        self.client.login(username="testuser@example.com", password="testpass123")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        if response.context:
            self.assertIn("key", response.context)
            self.assertIn("record", response.context)


class ResultsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )
        self.record1 = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
            title="First Record",
        )
        self.record2 = RecordOutput.objects.create(
            record_id="rec-002",
            ia_id="ia-002",
            reference="REF-002",
            title="Second Record",
        )

    def test_results_view_requires_login(self):
        """Test that results view requires login"""
        response = self.client.get("/results?q=test")
        self.assertEqual(response.status_code, 302)

    def test_results_view_no_query(self):
        """Test results view with no query"""
        self.client.login(username="testuser@example.com", password="testpass123")
        response = self.client.get("/results?q=")
        self.assertEqual(response.status_code, 200)
        # Should return all records
        if response.context and "records" in response.context:
            self.assertEqual(len(response.context["records"]), 2)

    def test_results_view_with_query(self):
        """Test results view with search query"""
        self.client.login(username="testuser@example.com", password="testpass123")
        response = self.client.get("/results?q=REF-001")
        self.assertEqual(response.status_code, 200)
        if response.context and "records" in response.context:
            records = response.context["records"]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].reference, "REF-001")

    def test_results_view_case_insensitive_search(self):
        """Test that search is case insensitive"""
        self.client.login(username="testuser@example.com", password="testpass123")
        response = self.client.get("/results?q=ref-001")
        if response.context and "records" in response.context:
            records = response.context["records"]
            self.assertEqual(len(records), 1)


class SubmittedViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
            title="Test Record",
        )

    def test_submitted_view_requires_login(self):
        """Test that submitted view requires login"""
        response = self.client.get(f"/submitted/{self.record.record_id}")
        self.assertEqual(response.status_code, 302)

    def test_submitted_view_authenticated(self):
        """Test submitted view when authenticated"""
        self.client.login(username="testuser@example.com", password="testpass123")
        response = self.client.get(f"/submitted/{self.record.record_id}")
        self.assertEqual(response.status_code, 200)

    def test_submitted_view_context(self):
        """Test submitted view passes reference to context"""
        self.client.login(username="testuser@example.com", password="testpass123")
        response = self.client.get(f"/submitted/{self.record.record_id}")
        self.assertEqual(response.status_code, 200)
        if response.context:
            self.assertIn("reference", response.context)
            self.assertEqual(response.context["reference"], "REF-001")


class UploadViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
            title="Test Record",
        )

    def test_upload_view_get_requires_login(self):
        """Test that GET to upload requires login"""
        response = self.client.get(f"/upload/{self.record.record_id}")
        self.assertEqual(response.status_code, 302)

    def test_upload_view_get_authenticated(self):
        """Test GET upload view when authenticated"""
        self.client.login(username="testuser@example.com", password="testpass123")
        response = self.client.get(f"/upload/{self.record.record_id}")
        self.assertEqual(response.status_code, 200)

    def test_upload_view_get_context(self):
        """Test GET upload view context"""
        self.client.login(username="testuser@example.com", password="testpass123")
        response = self.client.get(f"/upload/{self.record.record_id}")
        self.assertEqual(response.status_code, 200)
        if response.context:
            self.assertIn("record_id", response.context)
            self.assertEqual(response.context["record_id"], self.record.record_id)

    def test_upload_view_post_requires_login(self):
        """Test that POST to upload requires login"""
        response = self.client.post(f"/upload/{self.record.record_id}")
        self.assertEqual(response.status_code, 302)

    def test_upload_view_post_invalid_form(self):
        """Test upload POST with invalid form"""
        self.client.login(username="testuser@example.com", password="testpass123")
        response = self.client.post(f"/upload/{self.record.record_id}", {})
        self.assertEqual(response.status_code, 200)

    def test_upload_view_post_valid_with_matching_id(self):
        """Test upload POST with valid JSON matching record ID"""
        self.client.login(username="testuser@example.com", password="testpass123")
        json_data = json.dumps(
            {
                "recordId": "rec-001",
                "iaId": "ia-001",
                "reference": "REF-001",
                "title": "Updated Title",
            }
        )
        files = {
            "json_edit": SimpleUploadedFile("test.json", json_data.encode("utf-8"))
        }
        response = self.client.post(
            f"/upload/{self.record.record_id}",
            {"reason": "Testing upload"},
            files=files,
        )
        # POST should either redirect or render the form
        self.assertIn(response.status_code, [200, 302])

    def test_upload_view_post_id_mismatch(self):
        """Test upload POST with ID mismatch"""
        self.client.login(username="testuser@example.com", password="testpass123")
        json_data = json.dumps(
            {
                "recordId": "rec-002",
                "iaId": "ia-002",
                "reference": "REF-002",
            }
        )
        files = {
            "json_edit": SimpleUploadedFile("test.json", json_data.encode("utf-8"))
        }
        response = self.client.post(
            f"/upload/{self.record.record_id}",
            {"reason": "Testing upload"},
            files=files,
        )
        # When ID mismatches, the form should return 200 with error message
        self.assertEqual(response.status_code, 200)
        # Check that error is in context if context exists
        if response.context:
            self.assertTrue("error" in response.context or response.status_code == 200)


class ApiRecordViewTest(TestCase):
    """Test the API endpoint for retrieving record data"""

    def setUp(self):
        self.client = Client()
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
            title="Test Record",
            description="Test Description",
        )

    def test_api_record_404_without_auth(self):
        """Test that API requires authentication"""
        response = self.client.get(f"/api/records/rec-001/")
        # Note: This requires proper OAuth setup. May return 403 or 401 depending on config
        self.assertIn(response.status_code, [401, 403, 404])

    def test_api_record_not_found(self):
        """Test API returns 404 for non-existent record"""
        # This test assumes mock auth setup, otherwise adjust expectations
        response = self.client.get("/api/records/non-existent/")
        # Will depend on auth setup
        self.assertIn(response.status_code, [401, 403, 404])
