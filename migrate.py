import os

from django.core.management import execute_from_command_line

def lambda_handler(event, context):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "store.settings")
    execute_from_command_line([",", "makemigrations"])
    execute_from_command_line([",", "migrate"])
