import pytest
from pathlib import Path
from unittest.mock import patch

from epi_annotation.config import Config, Document, InputCfg, ModelCfg, PdfCfg, PromptCfg, RunCfg
from epi_annotation.extract import extract_text


def make_config(extractor="pymupdf", max_chars=None):
    return Config(
        input=InputCfg(data_dirs=["."]),
        pdf=PdfCfg(extractor=extractor, max_chars=max_chars),
        models=[ModelCfg(name="m", provider="openai", model_id="gpt-4o")],
        run=RunCfg(),
        prompt=PromptCfg(active="v1", versions={"v1": "prompts/system.md"}),
    )


def make_doc(doc_id="bulletin_01", path="bulletin_01.pdf"):
    return Document(document_id=doc_id, source_dir=".", path=path)


def test_extract_writes_cache_and_returns_text(tmp_path):
    cfg = make_config()
    doc = make_doc()

    with patch("epi_annotation.extract._extract_with_pymupdf", return_value="extracted text"):
        result = extract_text(doc, cfg, str(tmp_path))

    assert result == "extracted text"
    cache_file = tmp_path / "cache" / "text" / "bulletin_01.txt"
    assert cache_file.exists()
    assert cache_file.read_text() == "extracted text"


def test_second_call_reads_from_cache_without_re_extracting(tmp_path):
    cfg = make_config()
    doc = make_doc()

    cache_file = tmp_path / "cache" / "text" / "bulletin_01.txt"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text("cached text")

    with patch("epi_annotation.extract._extract_with_pymupdf") as mock_extract:
        result = extract_text(doc, cfg, str(tmp_path))

    mock_extract.assert_not_called()
    assert result == "cached text"


def test_empty_extracted_text_raises_descriptive_error(tmp_path):
    cfg = make_config()
    doc = make_doc()

    with patch("epi_annotation.extract._extract_with_pymupdf", return_value="   \n  "):
        with pytest.raises(ValueError, match="bulletin_01"):
            extract_text(doc, cfg, str(tmp_path))


def test_max_chars_truncates_text_before_caching(tmp_path):
    cfg = make_config(max_chars=10)
    doc = make_doc()

    with patch("epi_annotation.extract._extract_with_pymupdf", return_value="a" * 100):
        result = extract_text(doc, cfg, str(tmp_path))

    assert result == "a" * 10
    cache_file = tmp_path / "cache" / "text" / "bulletin_01.txt"
    assert len(cache_file.read_text()) == 10


def test_pdftotext_extractor_routes_to_pdftotext(tmp_path):
    cfg = make_config(extractor="pdftotext")
    doc = make_doc()

    with patch("epi_annotation.extract._extract_with_pdftotext", return_value="pdftotext output") as mock:
        result = extract_text(doc, cfg, str(tmp_path))

    mock.assert_called_once_with(doc.path)
    assert result == "pdftotext output"


@pytest.mark.skipif(
    not any(Path("data/raw/golden_standard_base").glob("*.pdf")),
    reason="No PDFs in data/raw/golden_standard_base",
)
def test_real_pdf_extraction_smoke_test(tmp_path):
    """Smoke: a real bulletin PDF produces non-empty text and creates a cache file."""
    cfg = make_config()
    pdf_path = next(Path("data/raw/golden_standard_base").glob("*.pdf"))
    doc = Document(document_id=pdf_path.stem, source_dir=str(pdf_path.parent), path=str(pdf_path))

    text = extract_text(doc, cfg, str(tmp_path))

    assert len(text) > 100
    cache_file = tmp_path / "cache" / "text" / f"{pdf_path.stem}.txt"
    assert cache_file.exists()
