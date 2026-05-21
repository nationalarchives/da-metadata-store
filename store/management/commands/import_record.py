import json
import os

from django.core.management.base import BaseCommand, CommandError

from ...import_record import import_record_payload


class Command(BaseCommand):
    help = "Import a RecordOutput JSON file"

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str)

    def handle(self, *args, **options):
        json_path = options["json_path"]
        for json_file in os.listdir(json_path):
            with open(f"{json_path}/{json_file}", "r", encoding="utf-8") as fh:
                payload = json.load(fh)
                record = import_record_payload(payload)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Imported record {record.record_id} ({record.reference})"
                    )
                )
