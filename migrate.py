import os

from django.core.management import execute_from_command_line


def lambda_handler(event, context):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "store.settings")
    execute_from_command_line([",", "makemigrations"])
    execute_from_command_line([",", "migrate"])
    execute_from_command_line([",", "loaddata", "change_reason"])
    if os.environ.get("TEST", "false") == "true":
        execute_from_command_line(
            [",", "loaddata", "tests/test_scripts/test-fixture.json"]
        )
