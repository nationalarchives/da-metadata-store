import logging
import os

import boto3
from django.conf import settings
from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgresDatabaseWrapper,
)

logger = logging.getLogger(__name__)


class DatabaseWrapper(PostgresDatabaseWrapper):
    """
    PostgreSQL backend that authenticates using a short-lived AWS IAM token
    rather than a static password.

    How it works:
      - boto3 calls the RDS API to generate a 15-minute auth token signed by
        the caller's IAM credentials (the Lambda execution role in production,
        your local AWS profile in development).
      - That token is injected as the password on every new connection.
      - SSL is required — RDS will reject IAM-authenticated connections without it.

    Prerequisites:
      1. IAM authentication enabled on the RDS instance.
      2. A PostgreSQL user created with the rds_iam attribute.
      3. The caller's IAM principal has rds-db:connect permission for that user.
    """

    def get_connection_params(self):
        params = super().get_connection_params()
        if os.environ.get("USE_IAM_AUTH", "false") == "true":
            region = os.environ.get("AWS_REGION", "eu-west-2")
            client = boto3.client("rds", region_name=region)
            token = client.generate_db_auth_token(
                DBHostname=params["host"],
                Port=params.get("port", 5432),
                DBUsername=params["user"],
            )

            params["password"] = token
            params["sslmode"] = "require"
        return params
