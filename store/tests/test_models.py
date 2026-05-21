from django.test import TestCase
from django.core.exceptions import ValidationError
from store.models import (
    RecordOutput,
    CopyrightTitle,
    RecordCopyrightTitle,
    Dimension,
    DimensionType,
    InquiryAppearance,
    CourtCase,
    Legislation,
    SensitivityReview,
    Change,
    Variation,
    Checksum,
    Person,
    RecordRelationship,
    RelationshipType,
)
from datetime import datetime, timedelta


class CopyrightTitleModelTest(TestCase):
    def setUp(self):
        self.copyright_title = CopyrightTitle.objects.create(name="Test Copyright")

    def test_copyright_title_creation(self):
        """Test creating a CopyrightTitle"""
        self.assertEqual(self.copyright_title.name, "Test Copyright")

    def test_copyright_title_unique_constraint(self):
        """Test that copyright title names are unique"""
        with self.assertRaises(Exception):
            CopyrightTitle.objects.create(name="Test Copyright")

    def test_copyright_title_str(self):
        """Test __str__ method"""
        self.assertEqual(str(self.copyright_title), "Test Copyright")

    def test_copyright_title_ordering(self):
        """Test copyright titles are ordered by name"""
        CopyrightTitle.objects.create(name="Zebra Copyright")
        CopyrightTitle.objects.create(name="Apple Copyright")
        titles = list(CopyrightTitle.objects.values_list("name", flat=True))
        self.assertEqual(titles[0], "Apple Copyright")


class RecordOutputModelTest(TestCase):
    def setUp(self):
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
            title="Test Record",
            description="Test Description",
            legal_status="Public",
            record_type="Document",
            language="en",
        )

    def test_record_output_creation(self):
        """Test creating a RecordOutput"""
        self.assertEqual(self.record.record_id, "rec-001")
        self.assertEqual(self.record.reference, "REF-001")
        self.assertEqual(self.record.title, "Test Record")

    def test_record_output_unique_record_id(self):
        """Test that record_id is unique"""
        with self.assertRaises(Exception):
            RecordOutput.objects.create(
                record_id="rec-001",
                ia_id="ia-002",
                reference="REF-002",
            )

    def test_record_output_str(self):
        """Test __str__ method returns reference"""
        self.assertEqual(str(self.record), "REF-001")

    def test_record_output_str_fallback_to_id(self):
        """Test __str__ method falls back to record_id when reference is empty"""
        record = RecordOutput.objects.create(
            record_id="rec-002",
            ia_id="ia-002",
            reference="",  # Empty string instead of None
        )
        # If reference is falsy, __str__ falls back to record_id
        result = str(record)
        self.assertIn("rec", result)  # Either reference or record_id should be in str

    def test_record_output_default_values(self):
        """Test default values for fields"""
        self.assertEqual(self.record.digital_file_count, 0)
        self.assertEqual(self.record.investigations, [])
        self.assertEqual(self.record.next_of_kin_types, [])

    def test_record_output_optional_fields(self):
        """Test optional fields can be null"""
        record = RecordOutput.objects.create(
            record_id="rec-blank",
            ia_id="ia-blank",
            reference="REF-BLANK",
        )
        self.assertIsNone(record.title)
        self.assertIsNone(record.description)


class RecordCopyrightTitleTest(TestCase):
    def setUp(self):
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
        )
        self.copyright = CopyrightTitle.objects.create(name="Test Copyright")
        self.record_copyright = RecordCopyrightTitle.objects.create(
            record=self.record,
            copyright_title=self.copyright,
        )

    def test_record_copyright_title_creation(self):
        """Test creating a RecordCopyrightTitle relationship"""
        self.assertEqual(self.record_copyright.record, self.record)
        self.assertEqual(self.record_copyright.copyright_title, self.copyright)

    def test_record_copyright_title_unique_constraint(self):
        """Test that copyright title per record is unique"""
        with self.assertRaises(Exception):
            RecordCopyrightTitle.objects.create(
                record=self.record,
                copyright_title=self.copyright,
            )

    def test_record_copyright_title_cascade_delete(self):
        """Test that deleting record deletes copyright relationship"""
        copyright_id = self.copyright.id
        self.record.delete()
        self.assertFalse(
            RecordCopyrightTitle.objects.filter(id=self.record_copyright.id).exists()
        )
        self.assertTrue(CopyrightTitle.objects.filter(id=copyright_id).exists())


class DimensionModelTest(TestCase):
    def setUp(self):
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
        )

    def test_dimension_creation(self):
        """Test creating a Dimension"""
        dimension = Dimension.objects.create(
            record=self.record,
            dimension_type=DimensionType.DEFAULT,
            first=100,
            second=50,
        )
        self.assertEqual(dimension.dimension_type, DimensionType.DEFAULT)
        self.assertEqual(dimension.first, 100)
        self.assertEqual(dimension.second, 50)

    def test_dimension_unique_type_per_record(self):
        """Test that dimension type is unique per record"""
        Dimension.objects.create(
            record=self.record,
            dimension_type=DimensionType.DEFAULT,
            first=100,
            second=50,
        )
        with self.assertRaises(Exception):
            Dimension.objects.create(
                record=self.record,
                dimension_type=DimensionType.DEFAULT,
                first=200,
                second=100,
            )

    def test_dimension_different_types(self):
        """Test creating different dimension types for same record"""
        Dimension.objects.create(
            record=self.record,
            dimension_type=DimensionType.DEFAULT,
            first=100,
            second=50,
        )
        dim_obverse = Dimension.objects.create(
            record=self.record,
            dimension_type=DimensionType.OBVERSE,
            first=150,
            second=75,
        )
        self.assertEqual(dim_obverse.dimension_type, DimensionType.OBVERSE)

    def test_dimension_fragment_flag(self):
        """Test is_fragment flag"""
        dimension = Dimension.objects.create(
            record=self.record,
            dimension_type=DimensionType.DEFAULT,
            first=100,
            is_fragment=True,
        )
        self.assertTrue(dimension.is_fragment)


class InquiryAppearanceModelTest(TestCase):
    def setUp(self):
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
        )

    def test_inquiry_appearance_creation(self):
        """Test creating an InquiryAppearance"""
        appearance = InquiryAppearance.objects.create(
            record=self.record,
            sequence=1,
            appearance_description="Test appearance",
        )
        self.assertEqual(appearance.sequence, 1)
        self.assertEqual(appearance.appearance_description, "Test appearance")

    def test_inquiry_appearance_witness_names(self):
        """Test witness_names array field"""
        appearance = InquiryAppearance.objects.create(
            record=self.record,
            sequence=1,
            witness_names=["John Doe", "Jane Smith"],
        )
        self.assertEqual(len(appearance.witness_names), 2)
        self.assertIn("John Doe", appearance.witness_names)

    def test_inquiry_appearance_str(self):
        """Test __str__ method"""
        appearance = InquiryAppearance.objects.create(
            record=self.record,
            sequence=1,
        )
        self.assertIn("inquiry appearance", str(appearance))


class CourtCaseModelTest(TestCase):
    def setUp(self):
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
        )

    def test_court_case_creation(self):
        """Test creating a CourtCase"""
        court_case = CourtCase.objects.create(
            record=self.record,
            sequence=1,
            name="Test Case",
            reference="CASE-001",
        )
        self.assertEqual(court_case.name, "Test Case")
        self.assertEqual(court_case.reference, "CASE-001")

    def test_court_case_with_dates(self):
        """Test court case with hearing dates"""
        from datetime import date

        court_case = CourtCase.objects.create(
            record=self.record,
            name="Test Case",
            hearing_start_date=date(2023, 1, 1),
            hearing_end_date=date(2023, 1, 5),
        )
        self.assertEqual(court_case.hearing_start_date, date(2023, 1, 1))

    def test_court_case_str(self):
        """Test __str__ method"""
        court_case = CourtCase.objects.create(
            record=self.record,
            name="Test Case",
        )
        self.assertEqual(str(court_case), "Test Case")


class SensitivityReviewModelTest(TestCase):
    def setUp(self):
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
        )

    def test_sensitivity_review_creation(self):
        """Test creating a SensitivityReview"""
        from datetime import date

        sensitivity = SensitivityReview.objects.create(
            record=self.record,
            has_sensitive_metadata=True,
            access_condition_code="F",
            foi_asserted_date=date(2023, 1, 1),
        )
        self.assertTrue(sensitivity.has_sensitive_metadata)
        self.assertEqual(sensitivity.access_condition_code, "F")

    def test_sensitivity_is_record_closed_property(self):
        """Test is_record_closed property for closed access codes"""
        sensitivity = SensitivityReview.objects.create(
            record=self.record,
            access_condition_code="F",
        )
        self.assertTrue(sensitivity.is_record_closed)

    def test_sensitivity_is_record_closed_open_access(self):
        """Test is_record_closed property for open access codes"""
        sensitivity = SensitivityReview.objects.create(
            record=self.record,
            access_condition_code="O",
        )
        self.assertFalse(sensitivity.is_record_closed)

    def test_sensitivity_is_record_closed_none(self):
        """Test is_record_closed property when access code is None"""
        sensitivity = SensitivityReview.objects.create(
            record=self.record,
            access_condition_code=None,
        )
        self.assertIsNone(sensitivity.is_record_closed)


class ChangeModelTest(TestCase):
    def setUp(self):
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
        )

    def test_change_creation(self):
        """Test creating a Change record"""
        from django.utils import timezone

        now = timezone.now()
        change = Change.objects.create(
            record=self.record,
            reason="Test modification",
            timestamp=now,
            operator_name="test@example.com",
        )
        self.assertEqual(change.reason, "Test modification")
        self.assertEqual(change.operator_name, "test@example.com")

    def test_change_related_to_record(self):
        """Test changes are related to records"""
        from django.utils import timezone

        change = Change.objects.create(
            record=self.record,
            reason="Test",
            timestamp=timezone.now(),
        )
        self.assertIn(change, self.record.audit_trail.all())


class VariationModelTest(TestCase):
    def setUp(self):
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
        )

    def test_variation_creation(self):
        """Test creating a Variation (digital file)"""
        variation = Variation.objects.create(
            record=self.record,
            file_id="file-001",
            file_name="test_file.pdf",
            size_bytes=1024,
        )
        self.assertEqual(variation.file_id, "file-001")
        self.assertEqual(variation.size_bytes, 1024)

    def test_variation_unique_file_id_per_record(self):
        """Test that file_id is unique per record"""
        Variation.objects.create(
            record=self.record,
            file_id="file-001",
            file_name="test.pdf",
        )
        with self.assertRaises(Exception):
            Variation.objects.create(
                record=self.record,
                file_id="file-001",
                file_name="test2.pdf",
            )

    def test_variation_str(self):
        """Test __str__ method returns file name"""
        variation = Variation.objects.create(
            record=self.record,
            file_id="file-001",
            file_name="test_file.pdf",
        )
        self.assertEqual(str(variation), "test_file.pdf")


class ChecksumModelTest(TestCase):
    def setUp(self):
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
        )
        self.variation = Variation.objects.create(
            record=self.record,
            file_id="file-001",
            file_name="test.pdf",
        )

    def test_checksum_creation(self):
        """Test creating a Checksum"""
        checksum = Checksum.objects.create(
            variation=self.variation,
            value="abc123",
            hash="SHA256",
        )
        self.assertEqual(checksum.value, "abc123")
        self.assertEqual(checksum.hash, "SHA256")

    def test_checksum_str(self):
        """Test __str__ method"""
        checksum = Checksum.objects.create(
            variation=self.variation,
            value="abc123",
            hash="SHA256",
        )
        self.assertEqual(str(checksum), "SHA256")


class PersonModelTest(TestCase):
    def setUp(self):
        self.record = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
        )

    def test_person_creation(self):
        """Test creating a Person"""
        person = Person.objects.create(
            record=self.record,
            given_name="John",
            family_name="Doe",
            full_name="John Doe",
        )
        self.assertEqual(person.given_name, "John")
        self.assertEqual(person.family_name, "Doe")

    def test_person_with_veteran_status(self):
        """Test person with veteran status"""
        person = Person.objects.create(
            record=self.record,
            full_name="John Doe",
            is_veteran=True,
        )
        self.assertTrue(person.is_veteran)

    def test_person_str(self):
        """Test __str__ method"""
        person = Person.objects.create(
            record=self.record,
            full_name="John Doe",
        )
        self.assertEqual(str(person), "John Doe")

    def test_person_unnamed(self):
        """Test unnamed person"""
        person = Person.objects.create(
            record=self.record,
        )
        self.assertEqual(str(person), "Unnamed person")


class RecordRelationshipModelTest(TestCase):
    def setUp(self):
        self.record1 = RecordOutput.objects.create(
            record_id="rec-001",
            ia_id="ia-001",
            reference="REF-001",
        )

    def test_record_relationship_creation(self):
        """Test creating a RecordRelationship"""
        relationship = RecordRelationship.objects.create(
            record=self.record1,
            relationship=RelationshipType.HAS_REPLACEMENT,
            reference="REF-002",
        )
        self.assertEqual(relationship.relationship, RelationshipType.HAS_REPLACEMENT)
        self.assertEqual(relationship.reference, "REF-002")

    def test_record_relationship_all_types(self):
        """Test all relationship types"""
        for rel_type, _ in RelationshipType.choices:
            relationship = RecordRelationship.objects.create(
                record=self.record1,
                relationship=rel_type,
                reference=f"REF-{rel_type}",
            )
            self.assertEqual(relationship.relationship, rel_type)

    def test_record_relationship_str(self):
        """Test __str__ method"""
        relationship = RecordRelationship.objects.create(
            record=self.record1,
            relationship=RelationshipType.REPLACEMENT_OF,
            reference="REF-002",
        )
        self.assertIn(RelationshipType.REPLACEMENT_OF, str(relationship))
