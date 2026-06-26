import pytest
from pydantic import ValidationError

from epi_annotation.schema import (
    Concern, Disease, DocumentAnnotation, NationalSignal, TerritorySignal, Trend,
)


VALID_TERRITORY = {
    "territory": "Minas Gerais",
    "disease": "dengue",
    "trend": "queda",
    "concern": "normal",
}

VALID_DOCUMENT = {
    "diseases_in_focus": ["dengue", "zika"],
    "national": [{"disease": "dengue", "trend": "alta", "concern": "muito_alta"}],
    "by_territory": [VALID_TERRITORY],
}


def test_document_annotation_parses_with_all_optional_fields_null():
    doc = DocumentAnnotation.model_validate({
        "reference_year": None,
        "publication_date": None,
        "diseases_in_focus": ["dengue"],
    })
    assert doc.diseases_in_focus == [Disease.dengue]
    assert doc.reference_year is None
    assert doc.national == []
    assert doc.by_territory == []


def test_document_annotation_parses_full_document():
    doc = DocumentAnnotation.model_validate(VALID_DOCUMENT)
    assert doc.national[0].disease == Disease.dengue
    assert doc.national[0].concern == Concern.very_high
    assert doc.by_territory[0].trend == Trend.decrease


def test_territory_signal_missing_disease_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        TerritorySignal.model_validate({
            "territory": "Minas Gerais",
            "trend": "queda",
            "concern": "normal",
        })
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("disease",) for e in errors)


def test_invalid_trend_enum_raises_validation_error():
    with pytest.raises(ValidationError):
        TerritorySignal.model_validate({**VALID_TERRITORY, "trend": "forte_alta"})


def test_invalid_disease_enum_raises_validation_error():
    with pytest.raises(ValidationError):
        TerritorySignal.model_validate({**VALID_TERRITORY, "disease": "malaria"})


def test_document_annotation_missing_diseases_in_focus_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        DocumentAnnotation.model_validate({"national": []})
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("diseases_in_focus",) for e in errors)


def test_national_signal_requires_concern():
    with pytest.raises(ValidationError) as exc_info:
        NationalSignal.model_validate({"disease": "dengue", "trend": "alta"})
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("concern",) for e in errors)
