from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve

from saml_auth.views import saml_acs, saml_login, saml_logout, saml_metadata, saml_sls

User = get_user_model()


class SamlRouteTests(TestCase):
    def test_url_resolution_for_saml_routes(self):
        self.assertIs(resolve("/saml/login").func, saml_login)
        self.assertIs(resolve("/saml/acs").func, saml_acs)
        self.assertIs(resolve("/saml/logout").func, saml_logout)
        self.assertIs(resolve("/saml/sls").func, saml_sls)
        self.assertIs(resolve("/saml/metadata").func, saml_metadata)

    @patch("saml_auth.views._build_saml_auth")
    def test_saml_login_redirects_to_identity_provider(self, mock_build_saml_auth):
        auth = Mock()
        auth.login.return_value = "https://idp.example.com/login"
        mock_build_saml_auth.return_value = auth

        response = self.client.get("/saml/login", {"next": "/results"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://idp.example.com/login")
        auth.login.assert_called_once_with(return_to="/results")

    def test_saml_acs_requires_post(self):
        response = self.client.get("/saml/acs")
        self.assertEqual(response.status_code, 405)

    @patch("saml_auth.views._build_saml_auth")
    def test_saml_acs_redirects_home_on_saml_errors(self, mock_build_saml_auth):
        auth = Mock()
        auth.get_errors.return_value = ["invalid_response"]
        auth.get_last_error_reason.return_value = "invalid signature"
        mock_build_saml_auth.return_value = auth

        response = self.client.post("/saml/acs", data={"SAMLResponse": "sample"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")
        auth.process_response.assert_called_once()

    @patch("saml_auth.views._build_saml_auth")
    def test_saml_acs_redirects_home_when_not_authenticated(self, mock_build_saml_auth):
        auth = Mock()
        auth.get_errors.return_value = []
        auth.is_authenticated.return_value = False
        mock_build_saml_auth.return_value = auth

        response = self.client.post("/saml/acs", data={"SAMLResponse": "sample"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")

    @patch("saml_auth.views._build_saml_auth")
    def test_saml_acs_logs_user_in_and_redirects_to_relay_state(self, mock_build_saml_auth):
        auth = Mock()
        auth.get_errors.return_value = []
        auth.is_authenticated.return_value = True
        auth.get_nameid.return_value = "user@example.com"
        auth.get_attributes.return_value = {
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname": ["Test"],
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname": ["User"],
        }
        mock_build_saml_auth.return_value = auth

        response = self.client.post("/saml/acs", data={"RelayState": "/results"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/results")
        self.assertTrue(User.objects.filter(username="user@example.com").exists())
        self.assertIn("_auth_user_id", self.client.session)

    @patch("saml_auth.views._build_saml_auth")
    def test_saml_logout_redirects_to_identity_provider(self, mock_build_saml_auth):
        auth = Mock()
        auth.logout.return_value = "https://idp.example.com/logout"
        mock_build_saml_auth.return_value = auth

        session = self.client.session
        session["samlNameId"] = "user@example.com"
        session["samlSessionIndex"] = "_session_index"
        session["samlNameIdFormat"] = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
        session.save()

        response = self.client.get("/saml/logout")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://idp.example.com/logout")
        auth.logout.assert_called_once()

    @patch("saml_auth.views._build_saml_auth")
    def test_saml_sls_redirects_home_on_errors(self, mock_build_saml_auth):
        auth = Mock()
        auth.process_slo.return_value = None
        auth.get_errors.return_value = ["slo_error"]
        mock_build_saml_auth.return_value = auth

        response = self.client.get("/saml/sls")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")

    @patch("saml_auth.views._build_saml_auth")
    def test_saml_sls_redirects_to_returned_url(self, mock_build_saml_auth):
        auth = Mock()
        auth.process_slo.return_value = "https://idp.example.com/post-logout"
        auth.get_errors.return_value = []
        mock_build_saml_auth.return_value = auth

        response = self.client.get("/saml/sls")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://idp.example.com/post-logout")

    @patch("saml_auth.views._build_saml_auth")
    def test_saml_sls_redirects_home_when_no_url(self, mock_build_saml_auth):
        auth = Mock()
        auth.process_slo.return_value = None
        auth.get_errors.return_value = []
        mock_build_saml_auth.return_value = auth

        response = self.client.get("/saml/sls")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")

    @patch("saml_auth.views.OneLogin_Saml2_Settings")
    def test_saml_metadata_returns_xml(self, mock_saml_settings_class):
        saml_settings = Mock()
        saml_settings.get_sp_metadata.return_value = "<xml>metadata</xml>"
        saml_settings.validate_metadata.return_value = []
        mock_saml_settings_class.return_value = saml_settings

        response = self.client.get("/saml/metadata")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/xml")
        self.assertEqual(response.content.decode(), "<xml>metadata</xml>")

    @patch("saml_auth.views.OneLogin_Saml2_Settings")
    def test_saml_metadata_returns_500_when_invalid(self, mock_saml_settings_class):
        saml_settings = Mock()
        saml_settings.get_sp_metadata.return_value = "<xml>metadata</xml>"
        saml_settings.validate_metadata.return_value = ["invalid"]
        mock_saml_settings_class.return_value = saml_settings

        response = self.client.get("/saml/metadata")

        self.assertEqual(response.status_code, 500)
        self.assertIn("Metadata errors", response.content.decode())
