import os
from django.core.management.base import BaseCommand
from django.db import connection

region = os.environ.get("AWS_DEFAULT_REGION", "eu-west-2")
account_number = os.environ.get("ACCOUNT_NUMBER", "")
environment = os.environ.get("ENVIRONMENT", "intg")

SQL = f"""
        CREATE OR REPLACE FUNCTION notify_catalogue_updates()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
                       payload json;
            lambda_arn text := 'arn:aws:lambda:{region}:{account_number}:function:{environment}-catalogue-updates';
                       BEGIN
            payload := json_build_object('record_id', NEW.id);
        
            PERFORM aws_lambda.invoke(
                aws_commons.create_lambda_function_arn(lambda_arn),
                payload
            );
        
                       RETURN NEW;
                       END;
        $$;
        """


class Command(BaseCommand):
    help = "Recreate database functions needed by the app"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute(SQL)
        self.stdout.write(self.style.SUCCESS("Database functions synced"))
