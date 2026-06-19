import pytest
from pydantic import ValidationError

from epi_annotation.schema import (
    AlertLevel, Disease, DocumentAnnotation, LocationLevel,
    SignalRow, Trend, VsExpected,
)


VALID_SIGNAL = {
    "disease": "dengue",
    "location_name": "Brasil",
    "location_level": "national",
    "trend": "decrease",
}

VALID_DOCUMENT = {
    "diseases_covered": ["dengue", "zika"],
    "signals": [VALID_SIGNAL],
}


def test_document_annotation_parses_with_all_optional_fields_null():
    doc = DocumentAnnotation.model_validate({
        "diseases_covered": ["dengue"],
        "reference_year": None,
        "publication_date": None,
        "bulletin_volume": None,
        "bulletin_number": None,
        "signals": [],
    })
    assert doc.diseases_covered == [Disease.dengue]
    assert doc.reference_year is None
    assert doc.signals == []


def test_document_annotation_parses_full_signal():
    doc = DocumentAnnotation.model_validate(VALID_DOCUMENT)
    sig = doc.signals[0]
    assert sig.disease == Disease.dengue
    assert sig.location_level == LocationLevel.national
    assert sig.probable_cases is None


def test_signal_missing_disease_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        SignalRow.model_validate({
            "location_name": "Brasil",
            "location_level": "national",
            "trend": "decrease",
        })
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("disease",) for e in errors)


def test_signal_invalid_disease_enum_raises_validation_error():
    with pytest.raises(ValidationError):
        SignalRow.model_validate({
            **VALID_SIGNAL,
            "disease": "malaria",
        })


def test_document_annotation_missing_diseases_covered_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        DocumentAnnotation.model_validate({"signals": []})
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("diseases_covered",) for e in errors)


def test_signal_optional_numeric_fields_accept_null():
    sig = SignalRow.model_validate({
        **VALID_SIGNAL,
        "probable_cases": None,
        "incidence_per_100k": None,
    })
    assert sig.probable_cases is None
    assert sig.incidence_per_100k is None


def test_sarampo_is_valid_disease():
    sig = SignalRow.model_validate({**VALID_SIGNAL, "disease": "sarampo"})
    assert sig.disease == Disease.sarampo
