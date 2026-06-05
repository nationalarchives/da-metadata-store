from django.test import TestCase

from store.models import Metadata, RelationshipTypes, Relationships, ChangeReason


class MetadataModelTest(TestCase):
    def setUp(self):
        self.metadata = Metadata.objects.create(
            id="meta-001",
            type="document",
            catalogue_reference="REF-001",
            metadata={"title": "Test Document", "description": "Test Description"},
        )

    def test_metadata_creation(self):
        self.assertEqual(self.metadata.id, "meta-001")
        self.assertEqual(self.metadata.type, "document")
        self.assertIn("title", self.metadata.metadata)

    def test_metadata_unique_id(self):
        with self.assertRaises(Exception):
            Metadata.objects.create(
                id="meta-001",
                type="document",
                metadata={},
            )

    def test_metadata_json_field(self):
        self.assertEqual(self.metadata.metadata["title"], "Test Document")

    def test_metadata_optional_fields(self):
        metadata = Metadata.objects.create(
            id="meta-002",
            type="record",
            metadata={},
        )
        self.assertIsNone(metadata.catalogue_reference)
        self.assertIsNone(metadata.is_mastered)
        self.assertIsNone(metadata.master_source)


class RelationshipTypesModelTest(TestCase):
    def test_relationship_types_creation(self):
        rel_type = RelationshipTypes.objects.create(
            type="has_replacement",
            to_label="replaces",
            from_label="replaced_by",
        )
        self.assertEqual(rel_type.type, "has_replacement")

    def test_relationship_types_labels(self):
        rel_type = RelationshipTypes.objects.create(
            type="parent_child",
            to_label="child",
            from_label="parent",
        )
        self.assertEqual(rel_type.to_label, "child")
        self.assertEqual(rel_type.from_label, "parent")


class RelationshipsModelTest(TestCase):
    def setUp(self):
        self.metadata1 = Metadata.objects.create(
            id="meta-001", type="document", metadata={"title": "Doc 1"}
        )
        self.metadata2 = Metadata.objects.create(
            id="meta-002", type="document", metadata={"title": "Doc 2"}
        )
        self.rel_type = RelationshipTypes.objects.create(
            type="has_replacement",
            to_label="replaces",
            from_label="replaced_by",
        )

    def test_relationships_creation(self):
        rel = Relationships.objects.create(
            from_asset=self.metadata1,
            to_asset=self.metadata2,
            type=self.rel_type,
        )
        self.assertEqual(rel.from_asset.id, "meta-001")
        self.assertEqual(rel.to_asset.id, "meta-002")
        self.assertEqual(rel.type, self.rel_type)

    def test_relationships_with_attributes(self):
        attributes = {"reason": "superseded"}
        rel = Relationships.objects.create(
            from_asset=self.metadata1,
            to_asset=self.metadata2,
            type=self.rel_type,
            attributes=attributes,
        )
        self.assertEqual(rel.attributes["reason"], "superseded")

    def test_relationships_cascade_delete(self):
        rel = Relationships.objects.create(
            from_asset=self.metadata1,
            to_asset=self.metadata2,
            type=self.rel_type,
        )
        rel_id = rel.id
        self.metadata1.delete()
        self.assertFalse(Relationships.objects.filter(id=rel_id).exists())


class RelationshipsQueryTest(TestCase):
    def setUp(self):
        self.meta1 = Metadata.objects.create(
            id="meta-001",
            type="document",
            metadata={"title": "Doc 1"},
        )
        self.meta2 = Metadata.objects.create(
            id="meta-002",
            type="document",
            metadata={"title": "Doc 2"},
        )
        self.rel_type = RelationshipTypes.objects.create(
            type="related_to",
            to_label="related",
            from_label="related_from",
        )

    def test_relationships_retrieval(self):
        Relationships.objects.create(
            from_asset=self.meta1,
            to_asset=self.meta2,
            type=self.rel_type,
        )
        rels = Relationships.objects.filter(from_asset=self.meta1)
        self.assertEqual(rels.count(), 1)
        self.assertEqual(rels.first().to_asset.id, "meta-002")


class ChangeReasonModelTest(TestCase):
    def test_change_reason_creation(self):
        reason = ChangeReason.objects.create(
            id="reason-001", reason="Closing an open record"
        )
        self.assertEqual(reason.id, "reason-001")
        self.assertEqual(reason.reason, "Closing an open record")

    def test_change_reason_unique_id(self):
        ChangeReason.objects.create(id="reason-001", reason="Test Reason")
        with self.assertRaises(Exception):
            ChangeReason.objects.create(id="reason-001", reason="Another Reason")

    def test_change_reason_text_field(self):
        reason = ChangeReason.objects.create(id="reason-test", reason="Test Reason")
        self.assertEqual(reason.reason, "Test Reason")
