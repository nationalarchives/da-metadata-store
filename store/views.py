import json
import logging
import os
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

from store.models import Metadata, Relationships
from store.validator import CognitoJWTBearerTokenValidator

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
        _validator = CognitoJWTBearerTokenValidator()
        require_auth.register_token_validator(_validator)
    return _validator



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
        f'https://prod-metadata-store.auth.eu-west-2.amazoncognito.com/logout?client_id={os.environ["COGNITO_CLIENT_ID"]}&redirect_uri={urllib.parse.quote_plus(app_base_url + "/")}&response_type=code'
    )


def pascal_to_title(text):
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', text).title()


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
    title_case_metadata = {}
    keys_to_title_case(title_case_metadata, metadata.metadata)
    title_case_metadata['Digital Files'] = sorted(title_case_metadata['Digital Files'], key=lambda x: int(x['Sort Order']))
    from_relationships = Relationships.objects.filter(from_asset__id=metadata.id)
    to_relationships = Relationships.objects.filter(to_asset__id=metadata.id)
    relationships = []
    relationships.extend([{'label': pascal_to_title(x.type.from_label), 'asset': x.to_asset } for x in from_relationships])
    relationships.extend([{'label': pascal_to_title(x.type.to_label), 'asset': x.from_asset } for x in to_relationships])

    return render(request, "record.html", {
        "metadata": title_case_metadata,
        "relationships": relationships
    })

class UploadForm(forms.Form):
    json_edit = forms.FileField()
    reason = forms.CharField()

def handle_uploaded_file(email, f, reason):
    loaded_json = json.load(f.file)
    record_id = loaded_json['recordId']
    metadata = Metadata.objects.get(id=record_id)
    old_metadata = metadata.metadata
    metadata.metadata = loaded_json
    metadata.save()
    changes = {'metadata': [json.dumps(old_metadata), json.dumps(loaded_json)]}
    LogEntry.objects.log_create(metadata, changes=changes, action=LogEntry.Action.UPDATE, actor_email=email, additional_data={'reason': reason})

@login_required
def upload(request, record_id):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.user.username, request.FILES["json_edit"], form.cleaned_data['reason'])
            return HttpResponseRedirect("/")

    return render(request, "upload.html", {"record_id": record_id})


@login_required
def submitted(request, record_id):
    record = Metadata.objects.get(id=record_id)
    return render(request, "submitted.html", {"reference": record.catalogue_reference})


@login_required
def home(request):
    return render(request, "search.html", {"key": None, "record": None})


@login_required
def results(request):
    query = request.GET.get('q', '')

    filtered_records = Metadata.objects.filter(
        Q(catalogue_reference__icontains=query)
    )
    return render(request, "results.html", {
        "key": query,
        "records": filtered_records
    })


@require_auth
def api_record(request, record_id):
    try:
        metadata = Metadata.objects.get(id=record_id)
        audit_logs = LogEntry.objects.get_for_object(metadata)
        audit = [{'email': x.actor_email, 'reason': x.additional_data['reason'], 'timestamp': x.timestamp } for x in audit_logs]
        response = {
            'metadata': metadata.metadata,
            'audit': audit
        }
    except Metadata.DoesNotExist:
        return JsonResponse({"error": "Record not found"}, status=404)

    return JsonResponse(response)
