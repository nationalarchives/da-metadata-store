from auditlog.registry import auditlog
from django.db import models
from django.db.models import CASCADE
from django.db.models.functions import Now

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models


class RelationshipType(models.TextChoices):
    REDACTION_OF = "RedactionOf", "RedactionOf"
    HAS_REDACTION = "HasRedaction", "HasRedaction"
    SEPARATED_MATERIAL = "SeparatedMaterial", "SeparatedMaterial"
    RELATED_MATERIAL = "RelatedMaterial", "RelatedMaterial"
    REPLACEMENT_OF = "ReplacementOf", "ReplacementOf"
    HAS_REPLACEMENT = "HasReplacement", "HasReplacement"


class DimensionType(models.TextChoices):
    DEFAULT = "default", "Default"
    OBVERSE = "obverse", "Obverse"
    REVERSE = "reverse", "Reverse"


class CopyrightTitle(models.Model):
    name = models.TextField(unique=True, db_index=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RecordOutput(models.Model):
    record_id = models.CharField(max_length=255, unique=True, verbose_name="Record ID")
    ia_id = models.CharField(max_length=255, db_index=True)
    reference = models.CharField(max_length=255, db_index=True)

    title = models.TextField(blank=True, null=True)
    translated_title = models.TextField(blank=True, null=True)
    public_title = models.TextField(blank=True, null=True)
    curated_title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    public_description = models.TextField(blank=True, null=True)
    former_reference_tna = models.TextField(blank=True, null=True)
    former_reference_department = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    tag = models.TextField(blank=True, null=True)
    arrangement = models.TextField(blank=True, null=True)
    public_arrangement = models.TextField(blank=True, null=True)

    tdr_consignment_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    tdr_file_reference = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    tdr_parent_reference = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    tdr_uuid = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    dri_batch_reference = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )

    source_internal_name = models.TextField(blank=True, null=True)
    connected_asset_note = models.TextField(blank=True, null=True)
    physical_description = models.TextField(blank=True, null=True)
    paper_number = models.CharField(max_length=255, blank=True, null=True)
    poor_law_union_number = models.CharField(max_length=255, blank=True, null=True)
    usage_restriction_description = models.TextField(blank=True, null=True)
    uk_government_web_archive = models.URLField(blank=True, null=True)

    legal_status = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    record_type = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    language = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    copyright_titles = models.ManyToManyField(
        CopyrightTitle,
        through="RecordCopyrightTitle",
        related_name="records",
        blank=True,
    )

    held_by = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    created_by = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    transferred_by = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )

    date_last_modified = models.DateTimeField(blank=True, null=True, db_index=True)
    curated_modified_at = models.DateTimeField(blank=True, null=True, db_index=True)

    curated_date_start = models.CharField(max_length=255, blank=True, null=True)
    curated_date_end = models.CharField(max_length=255, blank=True, null=True)
    curated_modified_at_note = models.TextField(blank=True, null=True)

    geographical_place = models.TextField(blank=True, null=True)
    covering_date_start = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    covering_date_end = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    provided_covering_date_start = models.CharField(
        max_length=255, blank=True, null=True
    )
    provided_covering_date_end = models.CharField(max_length=255, blank=True, null=True)
    provided_covering_date_text = models.TextField(blank=True, null=True)

    film_production_company_name = models.TextField(blank=True, null=True)
    film_title = models.TextField(blank=True, null=True)
    film_duration = models.DurationField(blank=True, null=True)

    evidence_provider = models.TextField(blank=True, null=True)

    investigations = ArrayField(
        base_field=models.TextField(),
        default=list,
        blank=True,
    )

    inquiry_hearing_date = models.DateField(blank=True, null=True, db_index=True)
    inquiry_session_description = models.TextField(blank=True, null=True)

    court_session = models.TextField(blank=True, null=True)
    court_session_date = models.DateField(blank=True, null=True, db_index=True)

    seal_owner_name = models.TextField(blank=True, null=True)
    seal_colour = models.CharField(max_length=255, blank=True, null=True)
    email_attachment_reference = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    seal_category = models.CharField(max_length=255, blank=True, null=True)

    image_sequence_end = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    image_sequence_start = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )

    dimension_text = models.TextField(blank=True, null=True)

    seal_start_date = models.CharField(max_length=255, blank=True, null=True)
    seal_end_date = models.CharField(max_length=255, blank=True, null=True)
    seal_obverse_start_date = models.CharField(max_length=255, blank=True, null=True)
    seal_obverse_end_date = models.CharField(max_length=255, blank=True, null=True)
    seal_reverse_start_date = models.CharField(max_length=255, blank=True, null=True)
    seal_reverse_end_date = models.CharField(max_length=255, blank=True, null=True)

    given_name = models.CharField(max_length=255, blank=True, null=True)
    family_name = models.CharField(max_length=255, blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.CharField(max_length=255, blank=True, null=True)
    birth_address = models.TextField(blank=True, null=True)
    national_registration_number = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    seaman_service_number = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )

    battalion_name = models.CharField(max_length=255, blank=True, null=True)
    next_of_kin_name = models.CharField(max_length=255, blank=True, null=True)
    next_of_kin_types = ArrayField(
        base_field=models.CharField(max_length=255),
        default=list,
        blank=True,
    )
    is_veteran = models.BooleanField(blank=True, null=True, db_index=True)

    note = models.TextField(blank=True, null=True)
    physical_condition_description = models.TextField(blank=True, null=True)
    reference_google_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    reference_parent_google_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    archivist_note = models.TextField(blank=True, null=True)
    archivist_note_date = models.CharField(max_length=255, blank=True, null=True)

    digital_file_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["reference", "record_id"]
        indexes = [
            models.Index(fields=["reference", "record_id"]),
            models.Index(fields=["record_type", "reference"]),
            models.Index(fields=["held_by", "reference"]),
        ]

    def __str__(self):
        return self.reference or self.record_id


class RecordCopyrightTitle(models.Model):
    record = models.ForeignKey(
        RecordOutput,
        on_delete=models.CASCADE,
        related_name="record_copyright_titles",
    )
    copyright_title = models.ForeignKey(
        CopyrightTitle,
        on_delete=models.CASCADE,
        related_name="record_copyright_titles",
    )

    class Meta:
        ordering = ["record", "copyright_title"]
        constraints = [
            models.UniqueConstraint(
                fields=["record", "copyright_title"],
                name="unique_copyright_title_per_record",
            )
        ]
        indexes = [
            models.Index(fields=["record", "copyright_title"]),
            models.Index(fields=["copyright_title", "record"]),
        ]

    def __str__(self):
        return f"{self.record.record_id} -> {self.copyright_title.name}"


class Dimension(models.Model):
    record = models.ForeignKey(
        RecordOutput,
        on_delete=models.CASCADE,
        related_name="dimensions",
    )
    dimension_type = models.CharField(max_length=20, choices=DimensionType.choices)
    first = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    second = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    is_fragment = models.BooleanField(default=False)

    class Meta:
        ordering = ["record", "dimension_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["record", "dimension_type"],
                name="unique_dimension_type_per_record",
            )
        ]

    def __str__(self):
        return f"{self.record.record_id}:{self.dimension_type}"


class InquiryAppearance(models.Model):
    record = models.ForeignKey(
        RecordOutput,
        on_delete=models.CASCADE,
        related_name="inquiry_appearances",
    )
    sequence = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        db_index=True,
    )
    witness_names = ArrayField(
        base_field=models.CharField(max_length=255),
        default=list,
        blank=True,
    )
    appearance_description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["record", "sequence", "id"]
        indexes = [
            models.Index(fields=["record", "sequence"]),
        ]

    def __str__(self):
        return f"{self.record.reference} inquiry appearance {self.sequence or self.pk}"


class CourtCase(models.Model):
    record = models.ForeignKey(
        RecordOutput,
        on_delete=models.CASCADE,
        related_name="court_cases",
    )
    sequence = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        db_index=True,
    )
    name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    reference = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    summary = models.TextField(blank=True, null=True)
    summary_judgment = models.TextField(blank=True, null=True)
    summary_reasons_for_judgment = models.TextField(blank=True, null=True)
    hearing_start_date = models.DateField(blank=True, null=True, db_index=True)
    hearing_end_date = models.DateField(blank=True, null=True, db_index=True)

    class Meta:
        ordering = ["record", "sequence", "id"]
        indexes = [
            models.Index(fields=["record", "sequence"]),
            models.Index(fields=["reference", "hearing_start_date"]),
        ]

    def __str__(self):
        return self.name or self.reference or f"CourtCase {self.pk}"


class Legislation(models.Model):
    url = models.URLField(unique=True)
    reference = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    class Meta:
        ordering = ["reference", "url"]

    def __str__(self):
        return self.reference or self.url


class SensitivityReview(models.Model):
    record = models.OneToOneField(
        RecordOutput,
        on_delete=models.CASCADE,
        related_name="sensitivity",
    )
    has_sensitive_metadata = models.BooleanField(default=False, db_index=True)
    foi_asserted_date = models.DateField(blank=True, null=True)
    sensitive_description = models.TextField(blank=True, null=True)
    access_condition_name = models.CharField(max_length=255, blank=True, null=True)
    access_condition_code = models.CharField(
        max_length=50, blank=True, null=True, db_index=True
    )
    closure_review_date = models.DateField(blank=True, null=True)
    closure_start_date = models.DateField(blank=True, null=True)
    closure_period = models.PositiveIntegerField(blank=True, null=True)
    closure_end_year = models.PositiveIntegerField(blank=True, null=True, db_index=True)
    foi_exemptions = models.ManyToManyField(
        Legislation,
        blank=True,
        related_name="sensitivity_reviews",
    )
    instrument_number = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    instrument_signed_date = models.DateField(blank=True, null=True)
    retention_reconsider_date = models.DateField(blank=True, null=True)
    ground_for_retention_code = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    ground_for_retention_description = models.TextField(blank=True, null=True)

    # Present in the C# source as [JsonIgnore]
    sensitive_name = models.CharField(max_length=255, blank=True, null=True)
    closure_description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["record"]

    @property
    def is_record_closed(self):
        if self.access_condition_code is None:
            return None
        return self.access_condition_code in {"F", "S", "T"}

    def __str__(self):
        return f"Sensitivity for {self.record.reference}"


class Change(models.Model):
    record = models.ForeignKey(
        RecordOutput,
        on_delete=models.CASCADE,
        related_name="audit_trail",
    )
    description_base64 = models.TextField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True, db_index=True)
    operator_name = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )

    class Meta:
        ordering = ["record", "timestamp", "id"]
        indexes = [
            models.Index(fields=["record", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.record.reference} change {self.timestamp or self.pk}"


class SensitivityReviewDiff(models.Model):
    change = models.OneToOneField(
        Change,
        on_delete=models.CASCADE,
        related_name="sensitivity",
    )

    # Expected shape: {"old": ..., "new": ...}
    foi_asserted_date = models.JSONField(blank=True, null=True)
    sensitive_name = models.JSONField(blank=True, null=True)
    sensitive_description = models.JSONField(blank=True, null=True)
    access_condition_name = models.JSONField(blank=True, null=True)
    access_condition_code = models.JSONField(blank=True, null=True)
    closure_review_date = models.JSONField(blank=True, null=True)
    closure_start_date = models.JSONField(blank=True, null=True)
    closure_period = models.JSONField(blank=True, null=True)
    closure_end_year = models.JSONField(blank=True, null=True)
    closure_description = models.JSONField(blank=True, null=True)
    foi_exemptions = models.JSONField(blank=True, null=True)
    instrument_number = models.JSONField(blank=True, null=True)
    instrument_signed_date = models.JSONField(blank=True, null=True)
    retention_reconsider_date = models.JSONField(blank=True, null=True)
    ground_for_retention_code = models.JSONField(blank=True, null=True)
    ground_for_retention_description = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Sensitivity diff for change {self.change_id}"


class Variation(models.Model):
    record = models.ForeignKey(
        RecordOutput,
        on_delete=models.CASCADE,
        related_name="digital_files",
    )
    file_id = models.CharField(max_length=255, db_index=True)
    file_name = models.CharField(max_length=500, db_index=True)
    size_bytes = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
    sort_order = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        db_index=True,
    )
    sequence = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        db_index=True,
    )
    file_path = models.TextField(blank=True, null=True)
    scanner_operator_identifier = models.CharField(
        max_length=255, blank=True, null=True
    )
    scanner_identifier = models.CharField(max_length=255, blank=True, null=True)
    scanner_geographical_place = models.CharField(max_length=255, blank=True, null=True)
    scanned_image_crop = models.CharField(max_length=255, blank=True, null=True)
    scanned_image_deskew = models.CharField(max_length=255, blank=True, null=True)
    scanned_image_split = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["record", "sort_order", "sequence", "id"]
        indexes = [
            models.Index(fields=["record", "sort_order"]),
            models.Index(fields=["record", "sequence"]),
            models.Index(fields=["file_id", "record"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["record", "file_id"],
                name="unique_file_id_per_record",
            )
        ]

    def __str__(self):
        return self.file_name


class Checksum(models.Model):
    variation = models.ForeignKey(
        Variation,
        on_delete=models.CASCADE,
        related_name="checksums",
    )
    value = models.TextField(blank=True, null=True)
    hash = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    class Meta:
        ordering = ["variation", "hash", "id"]
        indexes = [
            models.Index(fields=["variation", "hash"]),
        ]

    def __str__(self):
        return self.hash or f"Checksum {self.pk}"


class Person(models.Model):
    record = models.ForeignKey(
        RecordOutput,
        on_delete=models.CASCADE,
        related_name="people",
    )
    given_name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    family_name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    alternative_given_name = models.CharField(max_length=255, blank=True, null=True)
    alternative_family_name = models.CharField(max_length=255, blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    address = models.TextField(blank=True, null=True)
    birth_address = models.TextField(blank=True, null=True)
    parish = models.CharField(max_length=255, blank=True, null=True)
    town = models.CharField(max_length=255, blank=True, null=True)
    county = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    date_of_birth = models.CharField(max_length=255, blank=True, null=True)
    age = models.CharField(max_length=100, blank=True, null=True)
    national_registration_number = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    seaman_service_number = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    battalion_name = models.CharField(max_length=255, blank=True, null=True)
    navy_division_name = models.CharField(max_length=255, blank=True, null=True)
    next_of_kin_name = models.CharField(max_length=255, blank=True, null=True)
    next_of_kin_types = ArrayField(
        base_field=models.CharField(max_length=255),
        default=list,
        blank=True,
    )
    is_veteran = models.BooleanField(blank=True, null=True, db_index=True)

    class Meta:
        ordering = ["record", "family_name", "given_name", "id"]
        indexes = [
            models.Index(fields=["record", "family_name", "given_name"]),
            models.Index(fields=["record", "full_name"]),
        ]

    def __str__(self):
        return self.full_name or "Unnamed person"


class RecordRelationship(models.Model):
    record = models.ForeignKey(
        RecordOutput,
        on_delete=models.CASCADE,
        related_name="relationships",
    )
    relationship = models.CharField(
        max_length=50,
        choices=RelationshipType.choices,
        db_index=True,
    )
    reference = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["record", "relationship", "reference", "id"]
        indexes = [
            models.Index(fields=["record", "relationship"]),
            models.Index(fields=["reference", "relationship"]),
        ]

    def __str__(self):
        return f"{self.relationship}: {self.reference or 'no reference'}"
