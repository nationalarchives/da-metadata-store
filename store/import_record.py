import json
from datetime import timedelta
from pathlib import Path

from django.db import transaction

from .models import (
    Checksum,
    CopyrightTitle,
    RecordCopyrightTitle,
    RecordOutput,
    SensitivityReview,
    Variation,
)


def parse_duration(value):
    """
    Parse a duration if needed.

    Supports:
    - None
    - integer/float seconds
    - HH:MM:SS
    - HH:MM:SS.ssssss

    Returns timedelta or None.
    """
    if value in (None, ""):
        return None

    if isinstance(value, (int, float)):
        return timedelta(seconds=value)

    if isinstance(value, str):
        parts = value.split(":")
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            whole_seconds = int(seconds)
            microseconds = int((seconds - whole_seconds) * 1_000_000)
            return timedelta(
                hours=hours,
                minutes=minutes,
                seconds=whole_seconds,
                microseconds=microseconds,
            )

    raise ValueError(f"Unsupported duration value: {value!r}")


def set_copyright_titles(record, values):
    """
    Replace the record's copyright titles with the supplied list of names.
    """
    values = values or []

    RecordCopyrightTitle.objects.filter(record=record).delete()

    for raw_name in values:
        name = (raw_name or "").strip()
        if not name:
            continue

        title, _ = CopyrightTitle.objects.get_or_create(name=name)
        RecordCopyrightTitle.objects.get_or_create(
            record=record,
            copyright_title=title,
        )


@transaction.atomic
def import_record_payload(payload):
    """
    Import one JSON payload into the Django models.

    Returns the RecordOutput instance.
    """
    record, _created = RecordOutput.objects.update_or_create(
        record_id=payload["recordId"],
        defaults={
            "ia_id": payload["iaId"],
            "reference": payload["reference"],
            "title": payload.get("title"),
            "translated_title": payload.get("translatedTitle"),
            "public_title": payload.get("publicTitle"),
            "curated_title": payload.get("curatedTitle"),
            "description": payload.get("description"),
            "public_description": payload.get("publicDescription"),
            "former_reference_tna": payload.get("formerReferenceTna"),
            "former_reference_department": payload.get("formerReferenceDepartment"),
            "summary": payload.get("summary"),
            "tag": payload.get("tag"),
            "arrangement": payload.get("arrangement"),
            "public_arrangement": payload.get("publicArrangement"),
            "tdr_consignment_id": payload.get("tdrConsignmentId"),
            "tdr_file_reference": payload.get("tdrFileReference"),
            "tdr_parent_reference": payload.get("tdrParentReference"),
            "tdr_uuid": payload.get("tdrUuid"),
            "dri_batch_reference": payload.get("driBatchReference"),
            "source_internal_name": payload.get("sourceInternalName"),
            "connected_asset_note": payload.get("connectedAssetNote"),
            "physical_description": payload.get("physicalDescription"),
            "paper_number": payload.get("paperNumber"),
            "poor_law_union_number": payload.get("poorLawUnionNumber"),
            "usage_restriction_description": payload.get("usageRestrictionDescription"),
            "uk_government_web_archive": payload.get("ukGovernmentWebArchive"),
            "legal_status": payload.get("legalStatus"),
            "record_type": payload.get("recordType"),
            "language": payload.get("language"),
            "held_by": payload.get("heldBy"),
            "created_by": payload.get("createdBy"),
            "transferred_by": payload.get("transferredBy"),
            "date_last_modified": payload.get("dateLastModified"),
            "curated_modified_at": payload.get("curatedModifiedAt"),
            "curated_date_start": payload.get("curatedDateStart"),
            "curated_date_end": payload.get("curatedDateEnd"),
            "curated_modified_at_note": payload.get("curatedModifiedAtNote"),
            "geographical_place": payload.get("geographicalPlace"),
            "covering_date_start": payload.get("coveringDateStart"),
            "covering_date_end": payload.get("coveringDateEnd"),
            "provided_covering_date_start": payload.get("providedCoveringDateStart"),
            "provided_covering_date_end": payload.get("providedCoveringDateEnd"),
            "provided_covering_date_text": payload.get("providedCoveringDateText"),
            "film_production_company_name": payload.get("filmProductionCompanyName"),
            "film_title": payload.get("filmTitle"),
            "film_duration": parse_duration(payload.get("filmDuration")),
            "evidence_provider": payload.get("evidenceProvider"),
            "investigations": payload.get("investigations") or [],
            "inquiry_hearing_date": payload.get("inquiryHearingDate"),
            "inquiry_session_description": payload.get("inquirySessionDescription"),
            "court_session": payload.get("courtSession"),
            "court_session_date": payload.get("courtSessionDate"),
            "seal_owner_name": payload.get("sealOwnerName"),
            "seal_colour": payload.get("sealColour"),
            "email_attachment_reference": payload.get("emailAttachmentReference"),
            "seal_category": payload.get("sealCategory"),
            "image_sequence_end": payload.get("imageSequenceEnd"),
            "image_sequence_start": payload.get("imageSequenceStart"),
            "dimension_text": payload.get("dimensionText"),
            "seal_start_date": payload.get("sealStartDate"),
            "seal_end_date": payload.get("sealEndDate"),
            "seal_obverse_start_date": payload.get("sealObverseStartDate"),
            "seal_obverse_end_date": payload.get("sealObverseEndDate"),
            "seal_reverse_start_date": payload.get("sealReverseStartDate"),
            "seal_reverse_end_date": payload.get("sealReverseEndDate"),
            "given_name": payload.get("givenName"),
            "family_name": payload.get("familyName"),
            "full_name": payload.get("fullName"),
            "address": payload.get("address"),
            "date_of_birth": payload.get("dateOfBirth"),
            "birth_address": payload.get("birthAddress"),
            "national_registration_number": payload.get("nationalRegistrationNumber"),
            "seaman_service_number": payload.get("seamanServiceNumber"),
            "battalion_name": payload.get("battalionName"),
            "next_of_kin_name": payload.get("nextOfKinName"),
            "next_of_kin_types": payload.get("nextOfKinTypes") or [],
            "is_veteran": payload.get("isVeteran"),
            "note": payload.get("note"),
            "physical_condition_description": payload.get(
                "physicalConditionDescription"
            ),
            "reference_google_id": payload.get("referenceGoogleId"),
            "reference_parent_google_id": payload.get("referenceParentGoogleId"),
            "archivist_note": payload.get("archivistNote"),
            "archivist_note_date": payload.get("archivistNoteDate"),
            "digital_file_count": payload.get("digitalFileCount", 0),
        },
    )

    set_copyright_titles(record, payload.get("copyrightHolders"))

    sensitivity_payload = payload.get("sensitivity")
    if sensitivity_payload:
        sensitivity, _ = SensitivityReview.objects.update_or_create(
            record=record,
            defaults={
                "has_sensitive_metadata": sensitivity_payload.get(
                    "hasSensitiveMetadata", False
                ),
                "foi_asserted_date": sensitivity_payload.get("foiAssertedDate"),
                "sensitive_description": sensitivity_payload.get(
                    "sensitiveDescription"
                ),
                "access_condition_name": sensitivity_payload.get("accessConditionName"),
                "access_condition_code": sensitivity_payload.get("accessConditionCode"),
                "closure_review_date": sensitivity_payload.get("closureReviewDate"),
                "closure_start_date": sensitivity_payload.get("closureStartDate"),
                "closure_period": sensitivity_payload.get("closurePeriod"),
                "closure_end_year": sensitivity_payload.get("closureEndYear"),
                "instrument_number": sensitivity_payload.get("instrumentNumber"),
                "instrument_signed_date": sensitivity_payload.get(
                    "instrumentSignedDate"
                ),
                "retention_reconsider_date": sensitivity_payload.get(
                    "retentionReconsiderDate"
                ),
                "ground_for_retention_code": sensitivity_payload.get(
                    "groundForRetentionCode"
                ),
                "ground_for_retention_description": sensitivity_payload.get(
                    "groundForRetentionDescription"
                ),
                "sensitive_name": sensitivity_payload.get("sensitiveName"),
                "closure_description": sensitivity_payload.get("closureDescription"),
            },
        )

        # Replace legislation links if present.
        if "foiExemptions" in sensitivity_payload:
            sensitivity.foi_exemptions.clear()
            # Left intentionally minimal since your sample does not include foiExemptions.
            # Add get_or_create(Legislation, ...) here if you need it.

    else:
        SensitivityReview.objects.filter(record=record).delete()

    # Replace digital files on each import for this record.
    Variation.objects.filter(record=record).delete()

    for digital_file in payload.get("digitalFiles", []):
        variation = Variation.objects.create(
            record=record,
            file_id=digital_file["fileId"],
            file_name=digital_file["fileName"],
            size_bytes=digital_file.get("sizeBytes", 0),
            sort_order=digital_file.get("sortOrder"),
            sequence=digital_file.get("sequence"),
            file_path=digital_file.get("filePath"),
            scanner_operator_identifier=digital_file.get("scannerOperatorIdentifier"),
            scanner_identifier=digital_file.get("scannerIdentifier"),
            scanner_geographical_place=digital_file.get("scannerGeographicalPlace"),
            scanned_image_crop=digital_file.get("scannedImageCrop"),
            scanned_image_deskew=digital_file.get("scannedImageDeskew"),
            scanned_image_split=digital_file.get("scannedImageSplit"),
        )

        checksum_objects = [
            Checksum(
                variation=variation,
                value=checksum.get("value"),
                hash=checksum.get("hash"),
            )
            for checksum in digital_file.get("checksums", [])
        ]
        if checksum_objects:
            Checksum.objects.bulk_create(checksum_objects)

    return record


def import_record_file(path):
    """
    Import one JSON file from disk.
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return import_record_payload(payload)
