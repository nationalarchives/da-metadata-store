import json
import logging
import re
import urllib.parse

from auditlog.models import LogEntry

# noinspection PyUnresolvedReferences
from authlib.integrations.django_client import OAuth

# noinspection PyUnresolvedReferences
from authlib.integrations.django_oauth2 import ResourceProtector
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from store.models import Metadata, Relationships, ChangeReason
from store.validator import CognitoJWTBearerTokenValidator

logger = logging.getLogger(__name__)

app_base_url = settings.APP_BASE_URL
access_token_url = settings.ACCESS_TOKEN_URL
logout_base_url = settings.LOGOUT_BASE_URL
User = get_user_model()

oauth = OAuth()
oauth.register(
    name="cognito",
    server_metadata_url=f"{settings.ISSUER}/.well-known/openid-configuration",
    client_id=settings.CLIENT_ID,
    client_secret=settings.CLIENT_SECRET,
    access_token_url=access_token_url,
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
            # If validator initialization fails (e.g., missing keys in test environment),
            # we defer initialization until it's actually needed
            pass
    return _validator


get_validator()


def user_login(request):
    redirect_uri = request.build_absolute_uri(f"{app_base_url}/auth")
    return oauth.cognito.authorize_redirect(request, redirect_uri)


def auth(request):
    token = oauth.cognito.authorize_access_token(request)
    user_info = token["userinfo"]
    request.session["user"] = user_info
    email = user_info.get("email", user_info["sub"])
    first_name = user_info.get("given_name", "")
    last_name = user_info.get("family_name", "")
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
        f"{logout_base_url}/logout?client_id={settings.CLIENT_ID}&redirect_uri={urllib.parse.quote_plus(app_base_url + '/')}&response_type=code"
    )


def pascal_to_title(text):
    return re.sub(r"(?<!^)(?=[A-Z])", " ", text).title()


def keys_to_title_case(title_case_metadata, metadata):
    for key, value in metadata.items():
        if type(value) is list:
            list_metadata = []
            for l in value:
                each_metadata = {}
                keys_to_title_case(each_metadata, l)
                list_metadata.append(each_metadata)
                title_case_metadata[pascal_to_title(key)] = list_metadata
        elif type(value) is not dict:
            title_case_metadata[pascal_to_title(key)] = value
        else:
            dict_metadata = {}
            keys_to_title_case(dict_metadata, value)
            title_case_metadata[pascal_to_title(key)] = dict_metadata


@login_required
def records(request, record_uuid):
    metadata = Metadata.objects.get(id=record_uuid)
    title_case_metadata: dict[str, str] = {"Reference": metadata.catalogue_reference}
    keys_to_title_case(title_case_metadata, metadata.metadata)
    from_relationships = Relationships.objects.filter(from_asset__id=metadata.id)
    to_relationships = Relationships.objects.filter(to_asset__id=metadata.id)
    relationships = []
    relationships.extend(
        [
            {"label": pascal_to_title(x.type.from_label), "asset": x.to_asset}
            for x in from_relationships
        ]
    )
    relationships.extend(
        [
            {"label": pascal_to_title(x.type.to_label), "asset": x.from_asset}
            for x in to_relationships
        ]
    )

    return render(
        request,
        "record.html",
        {
            "id": record_uuid,
            "metadata": title_case_metadata,
            "relationships": relationships,
        },
    )


@login_required
def download(request, record_uuid):
    try:
        metadata = Metadata.objects.get(id=record_uuid)
    except Metadata.DoesNotExist:
        return JsonResponse({"error": "Record not found"}, status=404)

    json_response = JsonResponse(metadata.metadata, json_dumps_params={"indent": 2})
    json_response["Content-Disposition"] = f'attachment; filename="{record_uuid}.json"'
    return json_response


class UploadForm(forms.Form):
    json_edit = forms.FileField()
    reason = forms.CharField()


def handle_uploaded_file(email, f, reason, record_id):
    loaded_json = json.load(f.file)
    metadata = Metadata.objects.get(id=record_id)
    old_metadata = metadata.metadata
    metadata.metadata = loaded_json
    metadata.save()
    changes = {"metadata": [json.dumps(old_metadata), json.dumps(loaded_json)]}
    reason_row = ChangeReason.objects.get(id=reason)
    LogEntry.objects.log_create(
        metadata,
        changes=changes,
        action=LogEntry.Action.UPDATE,
        actor_email=email,
        additional_data={"reason": reason_row.reason},
    )


@login_required
def upload(request, record_id):
    errors = {}
    error_summary = []
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(
                request.user.username,
                request.FILES["json_edit"],
                form.cleaned_data["reason"],
                record_id,
            )
            return HttpResponseRedirect(
                reverse("submitted", kwargs={"record_id": record_id})
            )
        else:
            errors = form.errors
            if "json_edit" in errors:
                error_summary.append(
                    {"text": "A json file is required", "href": "#json_edit"}
                )
            if "reason" in errors:
                error_summary.append(
                    {"text": "A reason is required", "href": "#reason"}
                )
    change_reasons = ChangeReason.objects.all()
    reasons = [{"value": reason.id, "text": reason.reason} for reason in change_reasons]
    reasons.insert(0, {"value": "", "text": ""})
    return render(
        request,
        "upload.html",
        {
            "record_id": record_id,
            "reasons": reasons,
            "errors": errors,
            "error_summary": error_summary,
        },
    )


@login_required
def submitted(request, record_id):
    record = Metadata.objects.get(id=record_id)
    return render(request, "submitted.html", {"reference": record.catalogue_reference})


@login_required
def home(request):
    return render(request, "search.html", {"key": None, "record": None})


@login_required
def results(request):
    query = request.GET.get("q", "")

    filtered_records = Metadata.objects.filter(Q(catalogue_reference__icontains=query))
    return render(request, "results.html", {"key": query, "records": filtered_records})


@require_auth
def api_record(request, record_id):
    try:
        metadata = Metadata.objects.get(id=record_id)
        audit_logs = LogEntry.objects.get_for_object(metadata)
        audit = [
            {
                "email": x.actor_email,
                "reason": x.additional_data["reason"],
                "timestamp": x.timestamp,
            }
            for x in audit_logs
            if x.additional_data and "reason" in x.additional_data
        ]
        response = {"metadata": metadata.metadata, "audit": audit}
    except Metadata.DoesNotExist:
        return JsonResponse({"error": "Record not found"}, status=404)

    return JsonResponse(response)
