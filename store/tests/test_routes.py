from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import TestCase
from django.urls import resolve

from store.models import APIUser, Record
from store.views import api_record, home, records, results

User = get_user_model()


class StoreRouteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test-user@example.com",
            password="password123",
        )
        self.client.force_login(self.user)
        self.record = Record.objects.create(
            reference="ABC-123",
            name="Test record",
            description="Record description",
            data={"format": "json"},
        )

    def test_url_resolution_for_store_routes(self):
        self.assertIs(resolve("/").func, home)
        self.assertIs(resolve("/results").func, results)
        self.assertIs(resolve(f"/records/{self.record.reference}").func, records)
        self.assertIs(resolve(f"/api/records/{self.record.reference}").func, api_record)

    @patch("store.views.render", return_value=HttpResponse("ok"))
    def test_home_renders_search_template(self, mock_render):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        mock_render.assert_called_once()
        _, template_name, context = mock_render.call_args.args
        self.assertEqual(template_name, "search.html")
        self.assertEqual(context, {"key": None, "record": None})

    @patch("store.views.render", return_value=HttpResponse("ok"))
    def test_results_filters_records_by_query(self, mock_render):
        Record.objects.create(
            reference="XYZ/999",
            name="Other record",
            description="Another record",
            data={},
        )

        response = self.client.get("/results", {"q": "ABC"})

        self.assertEqual(response.status_code, 200)
        mock_render.assert_called_once()
        _, template_name, context = mock_render.call_args.args
        self.assertEqual(template_name, "results.html")
        self.assertEqual(context["key"], "ABC")
        self.assertEqual([r.reference for r in context["records"]], ["ABC-123"])

    @patch("store.views.render", return_value=HttpResponse("ok"))
    def test_records_renders_record_template(self, mock_render):
        response = self.client.get(f"/records/{self.record.reference}")

        self.assertEqual(response.status_code, 200)
        mock_render.assert_called_once()
        _, template_name, context = mock_render.call_args.args
        self.assertEqual(template_name, "record.html")
        self.assertEqual(context["record"], self.record)

    def test_api_record_returns_403_without_iam_identity(self):
        response = self.client.get(f"/api/records/{self.record.reference}")

        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(
            response.content,
            {"error": "IAM identity not found in request context"},
        )

    def test_api_record_returns_404_when_record_not_found(self):
        response = self.client.get(
            "/api/records/DOES-NOT-EXIST",
            **{
                "API_GATEWAY_AUTHORIZER": {
                    "iam": {
                        "userArn": "arn:aws:iam::123456789012:user/test-user",
                        "userId": "AIDAEXAMPLE",
                    }
                }
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(response.content, {"error": "Record not found"})
        self.assertTrue(APIUser.objects.filter(user_id="AIDAEXAMPLE").exists())

    def test_api_record_returns_record_and_upserts_api_user(self):
        response = self.client.get(
            f"/api/records/{self.record.reference}",
            **{
                "API_GATEWAY_AUTHORIZER": {
                    "iam": {
                        "userArn": "arn:aws:iam::123456789012:user/test-user",
                        "userId": "AIDAEXAMPLE",
                    }
                }
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "reference": self.record.reference,
                "name": self.record.name,
                "description": self.record.description,
                "data": self.record.data,
            },
        )
        api_user = APIUser.objects.get(user_id="AIDAEXAMPLE")
        self.assertEqual(api_user.user_arn, "arn:aws:iam::123456789012:user/test-user")

    def test_api_record_updates_existing_api_user(self):
        APIUser.objects.create(
            user_id="AIDAEXAMPLE",
            user_arn="arn:aws:iam::123456789012:user/old-user",
        )

        self.client.get(
            f"/api/records/{self.record.reference}",
            **{
                "API_GATEWAY_AUTHORIZER": {
                    "iam": {
                        "userArn": "arn:aws:iam::123456789012:user/new-user",
                        "userId": "AIDAEXAMPLE",
                    }
                }
            },
        )

        self.assertEqual(APIUser.objects.count(), 1)
        self.assertEqual(
            APIUser.objects.get(user_id="AIDAEXAMPLE").user_arn,
            "arn:aws:iam::123456789012:user/new-user",
        )
