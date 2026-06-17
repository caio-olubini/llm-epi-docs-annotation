import pytest
from pydantic import ValidationError

from epi_annotation.schema import Disease, DocumentAnnotation, EpiObservation, LocationLevel


VALID_OBSERVATION = {
    "disease": "dengue",
    "location_name": "Brasil",
    "location_level": "national",
}

VALID_DOCUMENT = {
    "diseases_covered": ["dengue", "zika"],
    "observations": [VALID_OBSERVATION],
}


def test_document_annotation_parses_with_all_optional_fields_null():
    doc = DocumentAnnotation.model_validate({
        "diseases_covered": ["dengue"],
        "reference_year": None,
        "publication_date": None,
        "bulletin_volume": None,
        "bulletin_number": None,
        "observations": [],
    })
    assert doc.diseases_covered == [Disease.dengue]
    assert doc.reference_year is None
    assert doc.observations == []


def test_document_annotation_parses_full_observation():
    doc = DocumentAnnotation.model_validate(VALID_DOCUMENT)
    obs = doc.observations[0]
    assert obs.disease == Disease.dengue
    assert obs.location_level == LocationLevel.national
    assert obs.probable_cases is None


def test_observation_missing_disease_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        EpiObservation.model_validate({
            "location_name": "Brasil",
            "location_level": "national",
        })
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("disease",) for e in errors)


def test_observation_invalid_disease_enum_raises_validation_error():
    with pytest.raises(ValidationError):
        EpiObservation.model_validate({
            **VALID_OBSERVATION,
            "disease": "malaria",
        })


def test_document_annotation_missing_diseases_covered_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        DocumentAnnotation.model_validate({"observations": []})
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("diseases_covered",) for e in errors)


def test_observation_optional_numeric_fields_accept_null():
    obs = EpiObservation.model_validate({
        **VALID_OBSERVATION,
        "probable_cases": None,
        "confirmed_cases": None,
        "deaths": None,
        "incidence_per_100k": None,
    })
    assert obs.probable_cases is None
    assert obs.incidence_per_100k is None
