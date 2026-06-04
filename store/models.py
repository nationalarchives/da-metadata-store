from auditlog.registry import auditlog
from django.db import models
from django.db.models import CASCADE
from django.db.models.functions import Now


class Metadata(models.Model):
    id = models.TextField(primary_key=True)
    catalogue_reference = models.TextField(blank=True, null=True)
    type = models.TextField()
    is_mastered = models.BooleanField(blank=True, null=True)
    master_source = models.TextField(blank=True, null=True)
    metadata = models.JSONField()
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(auto_now=True)


class RelationshipTypes(models.Model):
    type = models.CharField()
    to_label = models.CharField()
    from_label = models.CharField()
    is_acyclic = models.BooleanField


class Relationships(models.Model):
    from_asset = models.ForeignKey(Metadata, on_delete=CASCADE, related_name="+")
    to_asset = models.ForeignKey(Metadata, on_delete=CASCADE, related_name="+")
    type = models.ForeignKey(RelationshipTypes, on_delete=CASCADE)
    attributes = models.JSONField(blank=True, null=True)


class ChangeReason(models.Model):
    id = models.TextField(primary_key=True)
    reason = models.TextField(blank=False, null=False)


ChangeReason("043dee8b-afca-44c3-affb-6eabcaf4366e", "Closing an open record")
ChangeReason("1772f5ca-87a7-425b-9445-34eaf0083290", "Correction")
ChangeReason(
    "2b5a8e28-f6ea-40ec-ad65-ca91bda8ccf2", "Opening date later after FOI review"
)
ChangeReason("3fe3c78c-5514-4e82-949e-1b88d6120f90", "Ingest Closure")
ChangeReason(
    "47bbcf0c-384a-4bfe-a92f-1db791758e24", "Opening date earlier after FOI review"
)
ChangeReason(
    "4954be50-8583-4aa1-b0d0-1a8d80b43329",
    "Birth+marriage certificate record opening earlier",
)
ChangeReason(
    "5868b566-b3f7-49e5-976e-42bae9e2bb59", "Legacy: opening date later to match SAR"
)
ChangeReason("5c7f0f1c-c9d0-4942-95c1-3463f63018a4", "Record opened after review")
ChangeReason(
    "8583dcb1-9465-4f72-86fd-c73bbf1be916", "Legacy: record opened to match SAR"
)
ChangeReason("858b8791-80ee-453d-b0d5-70be693dd61e", "Sparql cleanup activity")
ChangeReason("924785a0-6275-4a6e-89ed-f011ae8fdebe", "Closure Update")
ChangeReason(
    "95760c91-0aad-41f5-a54e-ae8b0531ed82", "Death+marriage certificate record opening"
)
ChangeReason("9db26ba4-2058-4fea-8c8f-0fc527f8bd24", "Opened on export")
ChangeReason(
    "9ff9605a-14ec-4be8-8396-316aded86334", "Birth+marriage certificate record opening"
)
ChangeReason(
    "a7d669c4-e3a0-4f0e-95aa-dc8cef8ef8cf", "Opening a closed title or description"
)
ChangeReason(
    "a823ba2d-7eff-455d-951f-e48b28e966a6", "Closing an open title or description"
)
ChangeReason(
    "b674f54c-f0fb-11ea-adc1-0242ac120002",
    "Birth+marriage certificate record opening later",
)
ChangeReason("bb2194d1-3c4e-4ea1-8a53-2d99b16311a9", "FOI code amended after review")
ChangeReason(
    "f0c76bc6-1f56-44d1-bb02-d2cea8a1994e", "Legacy: opening date earlier to match SAR"
)


auditlog.register(Metadata)
