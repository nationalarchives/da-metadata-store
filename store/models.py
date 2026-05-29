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


auditlog.register(Metadata)