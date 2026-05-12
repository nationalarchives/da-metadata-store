import json
import logging

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from store.models import APIUser, Record

logger = logging.getLogger(__name__)

@login_required
def records(request, reference):
    record = Record.objects.get(reference=reference)
    return render(request, "record.html", {
        "record": record
    })

@login_required
def home(request):
    return render(request, "search.html", {
        "key": None,
        "record": None
    })

@login_required
def results(request):
    query = request.GET.get('q', '')

    filtered_records = Record.objects.filter(
        Q(reference__icontains=query) | Q(name__icontains=query)
    )
    return render(request, "results.html", {
        "key": query,
        "records": filtered_records
    })

@csrf_exempt
def api_record(request, reference):
    event = request.META.get("API_GATEWAY_AUTHORIZER", {})
    identity = event.get("iam", {})

    user_arn = identity.get("userArn")
    user_id = identity.get("userId")

    if not user_arn or not user_id:
        return JsonResponse({"error": "IAM identity not found in request context"}, status=403)

    api_user, created = APIUser.objects.update_or_create(
        user_id=user_id,
        defaults={"user_arn": user_arn},
    )
    if created:
        logger.info("Created new API user: %s", user_arn)

    try:
        record = Record.objects.get(reference=reference)
    except Record.DoesNotExist:
        return JsonResponse({"error": "Record not found"}, status=404)

    return JsonResponse({
        "reference": record.reference,
        "name": record.name,
        "description": record.description,
        "data": record.data,
    })
