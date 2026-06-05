from django.test import TestCase
from store.models import Metadata


class MetadataImportTest(TestCase):

    def test_metadata_creation_with_json(self):
        payload = {
            "id": "meta-001",
            "type": "document",
            "catalogue_reference": "REF-001",
            "metadata": {
                "title": "Test Document",
                "description": "A test document",
            },
        }
        metadata = Metadata.objects.create(
            id=payload["id"],
            type=payload["type"],
            catalogue_reference=payload["catalogue_reference"],
            metadata=payload["metadata"],
        )
        self.assertEqual(metadata.id, "meta-001")
        self.assertEqual(metadata.metadata["title"], "Test Document")

    def test_metadata_retrieval(self):
        Metadata.objects.create(
            id="meta-test",
            type="record",
            metadata={"title": "Test"},
        )
        retrieved = Metadata.objects.get(id="meta-test")
        self.assertEqual(retrieved.type, "record")

    def test_metadata_update(self):
        metadata = Metadata.objects.create(
            id="meta-update",
            type="document",
            metadata={"title": "Original"},
        )
        metadata.metadata["title"] = "Updated"
        metadata.save()

        retrieved = Metadata.objects.get(id="meta-update")
        self.assertEqual(retrieved.metadata["title"], "Updated")

    def test_metadata_bulk_import(self):
        payloads = [
            {"id": f"meta-{i}", "type": "document", "metadata": {"title": f"Doc {i}"}}
            for i in range(5)
        ]

        for payload in payloads:
            Metadata.objects.create(
                id=payload["id"],
                type=payload["type"],
                metadata=payload["metadata"],
            )

        self.assertEqual(Metadata.objects.count(), 5)

    def test_metadata_with_mastered_flag(self):
        metadata = Metadata.objects.create(
            id="meta-mastered",
            type="document",
            is_mastered=True,
            master_source="source-001",
            metadata={"title": "Mastered Document"},
        )
        self.assertTrue(metadata.is_mastered)
        self.assertEqual(metadata.master_source, "source-001")

    def test_metadata_timestamps(self):
        metadata = Metadata.objects.create(
            id="meta-time",
            type="document",
            metadata={"title": "Test"},
        )
        self.assertIsNotNone(metadata.created_at)
        self.assertIsNotNone(metadata.updated_at)
        self.assertLessEqual(
            metadata.created_at.strftime("yyyy-mm-dd"),
            metadata.updated_at.strftime("yyyy-mm-dd"),
        )

    def test_metadata_null_optional_fields(self):
        metadata = Metadata.objects.create(
            id="meta-minimal",
            type="record",
            metadata={},
        )
        self.assertIsNone(metadata.catalogue_reference)
        self.assertIsNone(metadata.is_mastered)
        self.assertIsNone(metadata.master_source)

    def test_metadata_complex_json_structure(self):
        complex_metadata = {
            "title": "Complex Document",
            "nested": {
                "field1": "value1",
                "field2": ["item1", "item2"],
            },
            "array": [1, 2, 3],
        }
        Metadata.objects.create(
            id="meta-complex",
            type="document",
            metadata=complex_metadata,
        )
        retrieved = Metadata.objects.get(id="meta-complex")
        self.assertEqual(retrieved.metadata["nested"]["field1"], "value1")
        self.assertEqual(len(retrieved.metadata["array"]), 3)

    def test_metadata_query_by_type(self):
        Metadata.objects.create(
            id="doc-001",
            type="document",
            metadata={"title": "Doc 1"},
        )
        Metadata.objects.create(
            id="rec-001",
            type="record",
            metadata={"title": "Rec 1"},
        )

        documents = Metadata.objects.filter(type="document")
        records = Metadata.objects.filter(type="record")

        self.assertEqual(documents.count(), 1)
        self.assertEqual(records.count(), 1)
