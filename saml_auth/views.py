import logging

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from django.conf import settings

logger = logging.getLogger(__name__)
User = get_user_model()


def get_saml_settings() -> dict:
    base_url = settings.APP_BASE_URL

    return {
        "strict": True,
        "debug": settings.DEBUG,
        "sp": {
            "entityId": f"{base_url}/saml/metadata",
            "assertionConsumerService": {
                "url": f"{base_url}/saml/acs",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "singleLogoutService": {
                "url": f"{base_url}/saml/sls",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
        },
        "idp": {
            "entityId": settings.SAML_IDP_ENTITY_ID,
            "singleSignOnService": {
                "url": settings.SAML_IDP_SSO_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": settings.SAML_IDP_SLO_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": settings.SAML_IDP_CERT,
        },
        "security": {
            # Azure AD signs responses; require it.
            "wantAssertionsSigned": False,
            "wantMessagesSigned": False,
            "authnRequestsSigned": False,
            "logoutRequestSigned": False,
            "logoutResponseSigned": False,
        },
    }

def _build_saml_auth(request) -> OneLogin_Saml2_Auth:
    """Construct a python3-saml Auth object from the current request."""
    req = {
        "https": "on" if request.is_secure() else "off",
        "http_host": settings.APP_BASE_URL.split("//")[1],
        "script_name": request.META["PATH_INFO"],
        "get_data": request.GET.copy(),
        "post_data": request.POST.copy(),
    }
    return OneLogin_Saml2_Auth(req, old_settings=get_saml_settings())


def _get_or_create_user(name_id: str, attributes: dict):
    email = name_id.lower().strip()
    first_name = _first(attributes.get(
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname", []))
    last_name = _first(attributes.get(
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname", []))

    user, created = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "first_name": first_name, "last_name": last_name},
    )
    if not created:
        updated = False
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if last_name and user.last_name != last_name:
            user.last_name = last_name
            updated = True
        if updated:
            user.save(update_fields=["first_name", "last_name"])
    return user


def _first(lst: list):
    return lst[0] if lst else ""


# ---------------------------------------------------------------------------
# SAML views
# ---------------------------------------------------------------------------

def saml_login(request):
    """Redirect the browser to Azure AD's SSO endpoint."""
    auth = _build_saml_auth(request)
    next_url = request.GET.get("next", "")
    return HttpResponseRedirect(auth.login(return_to=next_url))


@csrf_exempt
@require_http_methods(["POST"])
def saml_acs(request):
    """
    Assertion Consumer Service — Azure POSTs the SAML response here.
    Must be exempt from CSRF because Azure is posting cross-origin.
    """
    auth = _build_saml_auth(request)
    auth.process_response()

    errors = auth.get_errors()
    if errors:
        logger.error("SAML ACS error: %s — %s", errors, auth.get_last_error_reason())
        messages.error(request, "SSO login failed. Please try again.")
        return redirect("home")

    if not auth.is_authenticated():
        messages.error(request, "Authentication was not successful.")
        return redirect("home")

    user = _get_or_create_user(auth.get_nameid(), auth.get_attributes())
    user.backend = "django.contrib.auth.backends.ModelBackend"
    login(request, user)

    relay_state = request.POST.get("RelayState", "")
    if relay_state and relay_state.startswith("/"):
        return redirect(relay_state)
    return redirect("dashboard")


def saml_logout(request):
    """Initiate a SAML Single Logout."""
    auth = _build_saml_auth(request)
    name_id = request.session.get("samlNameId")
    session_index = request.session.get("samlSessionIndex")
    name_id_format = request.session.get("samlNameIdFormat")

    logout(request)
    return HttpResponseRedirect(
        auth.logout(
            name_id=name_id,
            session_index=session_index,
            name_id_format=name_id_format,
        )
    )


def saml_sls(request):
    """Single Logout Service — handles the IdP's logout response/request."""
    auth = _build_saml_auth(request)

    def delete_session(_msg_id, _attributes, _session_index, _name_id, _session,
                       _name_id_format, _name_id_nq, _name_id_spnq):
        logout(request)

    url = auth.process_slo(delete_session_cb=delete_session)
    errors = auth.get_errors()
    if errors:
        logger.error("SAML SLO error: %s", errors)
        return redirect("home")
    if url:
        return HttpResponseRedirect(url)
    return redirect("home")


def saml_metadata(request):
    """Expose the SP metadata XML so Azure can import it automatically."""
    sp_settings = OneLogin_Saml2_Settings(
        settings=get_saml_settings(), sp_validation_only=True
    )
    metadata = sp_settings.get_sp_metadata()
    errors = sp_settings.validate_metadata(metadata)
    if errors:
        return HttpResponse(f"Metadata errors: {errors}", status=500)
    return HttpResponse(metadata, content_type="text/xml")
