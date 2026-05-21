from datetime import timedelta

from django.test import TestCase

from store.import_record import (
    parse_duration,
    set_copyright_titles,
    import_record_payload,
)
from store.models import (
    RecordOutput,
    CopyrightTitle,
    SensitivityReview,
)


class ParseDurationTest(TestCase):
    def test_parse_duration_none(self):
        """Test parsing None"""
        result = parse_duration(None)
        self.assertIsNone(result)

    def test_parse_duration_empty_string(self):
        """Test parsing empty string"""
        result = parse_duration("")
        self.assertIsNone(result)

    def test_parse_duration_integer_seconds(self):
        """Test parsing integer seconds"""
        result = parse_duration(60)
        self.assertEqual(result, timedelta(seconds=60))

    def test_parse_duration_float_seconds(self):
        """Test parsing float seconds"""
        result = parse_duration(90.5)
        self.assertEqual(result, timedelta(seconds=90.5))

    def test_parse_duration_hms_format(self):
        """Test parsing HH:MM:SS format"""
        result = parse_duration("01:30:45")
        expected = timedelta(hours=1, minutes=30, seconds=45)
        self.assertEqual(result, expected)

    def test_parse_duration_hms_with_microseconds(self):
        """Test parsing HH:MM:SS.ssssss format"""
        result = parse_duration("01:30:45.500000")
        expected = timedelta(hours=1, minutes=30, seconds=45, microseconds=500000)
        self.assertEqual(result, expected)

    def test_parse_duration_invalid_format(self):
        """Test parsing invalid format raises error"""
        with self.assertRaises(ValueError):
            parse_duration("invalid")

    def test_parse_duration_zero(self):
        """Test parsing zero"""
        result = parse_duration(0)
        self.assertEqual(result, timedelta(seconds=0))


class SetCopyrightTitlesTest(TestCase):
    def setUp(self):
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
        )

    def test_set_copyright_titles_empty_list(self):
        """Test setting empty copyright titles"""
        set_copyright_titles(self.record, [])
        self.assertEqual(self.record.copyright_titles.count(), 0)

    def test_set_copyright_titles_none(self):
        """Test setting None as copyright titles"""
        set_copyright_titles(self.record, None)
        self.assertEqual(self.record.copyright_titles.count(), 0)

    def test_set_copyright_titles_single(self):
        """Test setting single copyright title"""
        set_copyright_titles(self.record, ["Test Copyright"])
        self.assertEqual(self.record.copyright_titles.count(), 1)
        self.assertEqual(self.record.copyright_titles.first().name, "Test Copyright")

    def test_set_copyright_titles_multiple(self):
        """Test setting multiple copyright titles"""
        titles = ["Copyright 1", "Copyright 2", "Copyright 3"]
        set_copyright_titles(self.record, titles)
        self.assertEqual(self.record.copyright_titles.count(), 3)
        for title in titles:
            self.assertTrue(self.record.copyright_titles.filter(name=title).exists())

    def test_set_copyright_titles_replaces_existing(self):
        """Test that setting titles replaces existing ones"""
        set_copyright_titles(self.record, ["Old Copyright"])
        self.assertEqual(self.record.copyright_titles.count(), 1)
        set_copyright_titles(self.record, ["New Copyright"])
        self.assertEqual(self.record.copyright_titles.count(), 1)
        self.assertEqual(self.record.copyright_titles.first().name, "New Copyright")

    def test_set_copyright_titles_ignores_empty_strings(self):
        """Test that empty strings are ignored"""
        set_copyright_titles(self.record, ["Valid", "", "  ", "Another"])
        self.assertEqual(self.record.copyright_titles.count(), 2)

    def test_set_copyright_titles_creates_copyright_if_not_exists(self):
        """Test that copyright titles are created if they don't exist"""
        set_copyright_titles(self.record, ["Brand New Copyright"])
        self.assertTrue(
            CopyrightTitle.objects.filter(name="Brand New Copyright").exists()
        )

    def test_set_copyright_titles_reuses_existing_copyright(self):
        """Test that existing copyright titles are reused"""
        copyright = CopyrightTitle.objects.create(name="Existing Copyright")
        set_copyright_titles(self.record, ["Existing Copyright"])
        self.assertEqual(
            CopyrightTitle.objects.filter(name="Existing Copyright").count(), 1
        )


class ImportRecordPayloadTest(TestCase):
    def setUp(self):
        self.minimal_payload = {
            "recordId": "rec-001",
            "iaId": "ia-001",
            "reference": "REF-001",
        }

    def test_import_record_payload_minimal(self):
        """Test importing minimal record payload"""
        record = import_record_payload(self.minimal_payload)
        self.assertEqual(record.record_id, "rec-001")
        self.assertEqual(record.ia_id, "ia-001")
        self.assertEqual(record.reference, "REF-001")

    def test_import_record_payload_creates_new_record(self):
        """Test that importing creates a new record if it doesn't exist"""
        self.assertFalse(RecordOutput.objects.filter(record_id="rec-001").exists())
        import_record_payload(self.minimal_payload)
        self.assertTrue(RecordOutput.objects.filter(record_id="rec-001").exists())

    def test_import_record_payload_updates_existing(self):
        """Test that importing updates existing record"""
        # Create a record using snake_case field names
        record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
        )
        payload = self.minimal_payload.copy()
        payload["title"] = "Updated Title"
        updated_record = import_record_payload(payload)
        self.assertEqual(updated_record.id, record.id)
        self.assertEqual(updated_record.title, "Updated Title")

    def test_import_record_payload_with_titles(self):
        """Test importing record with multiple titles"""
        payload = self.minimal_payload.copy()
        payload["title"] = "Main Title"
        payload["translatedTitle"] = "Translated Title"
        payload["publicTitle"] = "Public Title"
        payload["curatedTitle"] = "Curated Title"

        record = import_record_payload(payload)
        self.assertEqual(record.title, "Main Title")
        self.assertEqual(record.translated_title, "Translated Title")
        self.assertEqual(record.public_title, "Public Title")
        self.assertEqual(record.curated_title, "Curated Title")

    def test_import_record_payload_with_copyright_holders(self):
        """Test importing record with copyright holders"""
        payload = self.minimal_payload.copy()
        payload["copyrightHolders"] = ["Copyright Holder 1", "Copyright Holder 2"]

        record = import_record_payload(payload)
        self.assertEqual(record.copyright_titles.count(), 2)

    def test_import_record_payload_with_sensitivity(self):
        """Test importing record with sensitivity information"""
        payload = self.minimal_payload.copy()
        payload["sensitivity"] = {
            "hasSensitiveMetadata": True,
            "accessConditionCode": "F",
            "foiAssertedDate": "2023-01-01",
        }

        record = import_record_payload(payload)
        sensitivity = SensitivityReview.objects.get(record=record)
        self.assertTrue(sensitivity.has_sensitive_metadata)
        self.assertEqual(sensitivity.access_condition_code, "F")

    def test_import_record_payload_with_digital_files(self):
        """Test importing record with digital files"""
        payload = self.minimal_payload.copy()
        payload["digitalFiles"] = [
            {
                "fileId": "file-001",
                "fileName": "document.pdf",
                "sizeBytes": 1024,
                "sortOrder": 1,
            },
            {
                "fileId": "file-002",
                "fileName": "image.jpg",
                "sizeBytes": 2048,
                "sortOrder": 2,
            },
        ]

        record = import_record_payload(payload)
        self.assertEqual(record.digital_files.count(), 2)

    def test_import_record_payload_with_checksums(self):
        """Test importing record with file checksums"""
        payload = self.minimal_payload.copy()
        payload["digitalFiles"] = [
            {
                "fileId": "file-001",
                "fileName": "document.pdf",
                "sizeBytes": 1024,
                "checksums": [
                    {"value": "abc123", "hash": "SHA256"},
                    {"value": "def456", "hash": "MD5"},
                ],
            }
        ]

        record = import_record_payload(payload)
        variation = record.digital_files.first()
        self.assertEqual(variation.checksums.count(), 2)

    def test_import_record_payload_replaces_digital_files(self):
        """Test that digital files are replaced on each import"""
        # First import
        payload = self.minimal_payload.copy()
        payload["digitalFiles"] = [
            {"fileId": "file-001", "fileName": "doc1.pdf", "sizeBytes": 1024}
        ]
        record = import_record_payload(payload)
        self.assertEqual(record.digital_files.count(), 1)

        # Second import with different files
        payload["digitalFiles"] = [
            {"fileId": "file-002", "fileName": "doc2.pdf", "sizeBytes": 2048},
            {"fileId": "file-003", "fileName": "doc3.pdf", "sizeBytes": 3072},
        ]
        record = import_record_payload(payload)
        self.assertEqual(record.digital_files.count(), 2)

    def test_import_record_payload_with_dates(self):
        """Test importing record with various date fields"""
        payload = self.minimal_payload.copy()
        payload["coveringDateStart"] = "1900-01-01"
        payload["coveringDateEnd"] = "1950-12-31"
        payload["inquiryHearingDate"] = "2020-06-15"

        record = import_record_payload(payload)
        self.assertEqual(record.covering_date_start, "1900-01-01")
        self.assertEqual(record.covering_date_end, "1950-12-31")

    def test_import_record_payload_with_arrays(self):
        """Test importing record with array fields"""
        payload = self.minimal_payload.copy()
        payload["investigations"] = ["Investigation 1", "Investigation 2"]
        payload["nextOfKinTypes"] = ["Spouse", "Child"]

        record = import_record_payload(payload)
        self.assertEqual(record.investigations, ["Investigation 1", "Investigation 2"])
        self.assertEqual(record.next_of_kin_types, ["Spouse", "Child"])

    def test_import_record_payload_with_film_duration(self):
        """Test importing record with film duration"""
        payload = self.minimal_payload.copy()
        payload["filmDuration"] = "01:30:00"

        record = import_record_payload(payload)
        expected = timedelta(hours=1, minutes=30)
        self.assertEqual(record.film_duration, expected)

    def test_import_record_payload_clears_sensitivity_if_not_provided(self):
        """Test that sensitivity is cleared if not in payload"""
        # First import with sensitivity
        payload = self.minimal_payload.copy()
        payload["sensitivity"] = {
            "hasSensitiveMetadata": True,
            "accessConditionCode": "F",
        }
        record = import_record_payload(payload)
        self.assertTrue(SensitivityReview.objects.filter(record=record).exists())

        # Second import without sensitivity
        payload_without_sensitivity = self.minimal_payload.copy()
        record = import_record_payload(payload_without_sensitivity)
        self.assertFalse(SensitivityReview.objects.filter(record=record).exists())

    def test_import_record_payload_complex_full_record(self):
        """Test importing a complex full record"""
        payload = {
            "recordId": "rec-complex",
            "iaId": "ia-complex",
            "reference": "REF-COMPLEX",
            "title": "Complex Record",
            "description": "A complex test record",
            "legalStatus": "Public",
            "recordType": "Document",
            "language": "en",
            "copyrightHolders": ["Copyright Holder"],
            "heldBy": "National Archives",
            "createdBy": "Test Creator",
            "coveringDateStart": "1900-01-01",
            "coveringDateEnd": "1950-12-31",
            "digitalFileCount": 3,
            "sensitivity": {
                "hasSensitiveMetadata": False,
                "accessConditionCode": "O",
            },
            "digitalFiles": [
                {
                    "fileId": "file-001",
                    "fileName": "document.pdf",
                    "sizeBytes": 1024,
                    "sortOrder": 1,
                    "checksums": [{"value": "abc123", "hash": "SHA256"}],
                },
                {
                    "fileId": "file-002",
                    "fileName": "image.jpg",
                    "sizeBytes": 2048,
                    "sortOrder": 2,
                },
            ],
            "investigations": ["Investigation 1"],
        }

        record = import_record_payload(payload)

        # Verify all fields
        self.assertEqual(record.record_id, "rec-complex")
        self.assertEqual(record.title, "Complex Record")
        self.assertEqual(record.copyright_titles.count(), 1)
        self.assertEqual(record.digital_files.count(), 2)
        self.assertEqual(record.digital_files.first().checksums.count(), 1)
        self.assertEqual(record.investigations, ["Investigation 1"])

        sensitivity = SensitivityReview.objects.get(record=record)
        self.assertFalse(sensitivity.has_sensitive_metadata)
        self.assertEqual(sensitivity.access_condition_code, "O")

    def test_import_record_payload_default_array_values(self):
        """Test that default empty arrays are set correctly"""
        record = import_record_payload(self.minimal_payload)
        self.assertEqual(record.investigations, [])
        self.assertEqual(record.next_of_kin_types, [])

    def test_import_record_payload_integer_defaults(self):
        """Test that integer fields have proper defaults"""
        record = import_record_payload(self.minimal_payload)
        self.assertEqual(record.digital_file_count, 0)
