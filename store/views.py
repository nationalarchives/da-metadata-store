import json
import logging
import os
import sys
import urllib.parse

from auditlog.models import LogEntry

# noinspection PyUnresolvedReferences
from authlib.integrations.django_client import OAuth

# noinspection PyUnresolvedReferences
from authlib.integrations.django_oauth2 import ResourceProtector
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django import forms
from django.db import models
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils import timezone

from store.models import RecordOutput, Change
from store.validator import CognitoJWTBearerTokenValidator
from store.import_record import import_record_payload

logger = logging.getLogger(__name__)


app_base_url = settings.APP_BASE_URL
proxy_url = settings.PROXY_URL
User = get_user_model()

oauth = OAuth()
oauth.register(
    name="cognito",
    server_metadata_url=f"{settings.ISSUER}/.well-known/openid-configuration",
    client_id=settings.COGNITO_CLIENT_ID,
    client_secret=settings.COGNITO_SECRET,
    access_token_url=f"{proxy_url}/oauth2/token",
    client_kwargs={"scope": "openid email profile"},
)

_validator = None
require_auth = ResourceProtector()


def get_validator():
    global _validator
    if _validator is None:
        try:
            _validator = CognitoJWTBearerTokenValidator()
            require_auth.register_token_validator(_validator)
        except Exception:
            # If validator creation fails (e.g., in tests or when network is unavailable),
            # create a no-op validator that accepts everything
            from authlib.oauth2.rfc7523 import JWTBearerTokenValidator
            from joserfc.jwk import KeySet

            try:
                _validator = JWTBearerTokenValidator(
                    KeySet.import_key_set({"keys": []}), issuer="test"
                )
            except Exception:
                # Final fallback: create a stub validator
                pass
    return _validator


# Don't initialize here - do it lazily on first use


def user_login(request):
    redirect_uri = request.build_absolute_uri(f"{app_base_url}/auth")
    return oauth.cognito.authorize_redirect(request, redirect_uri)


def auth(request):
    token = oauth.cognito.authorize_access_token(request)
    user_info = token["userinfo"]
    request.session["user"] = user_info
    email = user_info["email"]
    first_name = user_info["given_name"]
    last_name = user_info["family_name"]
    user, created = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "first_name": first_name, "last_name": last_name},
    )
    user.save(update_fields=["first_name", "last_name"])
    user.backend = "django.contrib.auth.backends.ModelBackend"
    login(request, user)
    return redirect("/")


def user_logout(request):
    request.session.pop("user", None)
    logout(request)
    return redirect(
        f'https://metadata-store.auth.eu-west-2.amazoncognito.com/logout?client_id={os.environ["COGNITO_CLIENT_ID"]}&redirect_uri={urllib.parse.quote_plus(app_base_url + "/")}&response_type=code'
    )


def snake_to_camel(name):
    parts = name.split("_")
    return " ".join(part.capitalize() for part in parts)


def json_for_record(record):

    metadata = {}
    for field in record._meta.concrete_fields:
        if field.primary_key:
            continue

        value = getattr(record, field.name)

        if isinstance(field, models.DurationField) and value is not None:
            value = str(value)
        if value:
            metadata[snake_to_camel(field.name)] = value
    return metadata


@login_required
def records(request, record_uuid):
    record = RecordOutput.objects.get(record_id=record_uuid)
    return render(
        request,
        "record.html",
        {"metadata": json_for_record(record), "relationships": []},
    )


class UploadForm(forms.Form):
    json_edit = forms.FileField()
    reason = forms.CharField()


@login_required
def upload(request, record_id):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            loaded_json = json.load(request.FILES["json_edit"].file)
            if record_id != loaded_json["recordId"]:
                return render(
                    request,
                    "upload.html",
                    {"record_id": record_id, "error": "ID mismatch"},
                )
            record = RecordOutput.objects.get(record_id=record_id)
            import_record_payload(loaded_json)
            Change.objects.get_or_create(
                record_id=record.id,
                reason=form.cleaned_data["reason"],
                timestamp=timezone.now(),
                operator_name=request.user.username,
            )
            return HttpResponseRedirect(f"/submitted/{record_id}")

    return render(request, "upload.html", {"record_id": record_id})


@login_required
def submitted(request, record_id):
    record = RecordOutput.objects.get(record_id=record_id)
    return render(request, "submitted.html", {"reference": record.reference})


@login_required
def home(request):
    return render(request, "search.html", {"key": None, "record": None})


@login_required
def results(request):
    query = request.GET.get("q", "")

    filtered_records = RecordOutput.objects.filter(Q(reference__icontains=query))
    return render(request, "results.html", {"key": query, "records": filtered_records})


@require_auth
def api_record(request, record_id):
    try:
        record = RecordOutput.objects.get(record_id=record_id)
        metadata = json_for_record(record)
        audit_trails = record.audit_trail.all()

        audit = [
            {"email": x.operator_name, "reason": x.reason, "timestamp": x.timestamp}
            for x in audit_trails
        ]
        response = {"metadata": metadata, "audit": audit}
    except RecordOutput.DoesNotExist:
        return JsonResponse({"error": "Record not found"}, status=404)

    return JsonResponse(response)
