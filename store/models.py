from django.db import models


class Record(models.Model):
    reference = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255, null=True)
    description = models.CharField(max_length=255, null=True)
    data = models.JSONField()

    def __str__(self):
        return self.reference


class APIUser(models.Model):
    user_id = models.CharField(max_length=255, unique=True, db_index=True)
    user_arn = models.CharField(max_length=1024)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user_arn
