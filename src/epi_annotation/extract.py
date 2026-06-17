import subprocess
from pathlib import Path

from epi_annotation.config import Config, Document


def extract_text(doc: Document, cfg: Config, run_dir: str) -> str:
    cache_path = Path(run_dir) / "cache" / "text" / f"{doc.document_id}.txt"

    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    text = _extract_from_pdf(doc.path, cfg)

    if not text.strip():
        raise ValueError(f"Extracted text is empty for document '{doc.document_id}' ({doc.path})")

    if cfg.pdf.max_chars is not None:
        text = text[: cfg.pdf.max_chars]

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(text, encoding="utf-8")

    return text


def _extract_from_pdf(path: str, cfg: Config) -> str:
    if cfg.pdf.extractor == "pdftotext":
        return _extract_with_pdftotext(path)
    return _extract_with_pymupdf(path)


def _extract_with_pymupdf(path: str) -> str:
    import fitz  # pymupdf

    with fitz.open(path) as pdf:
        return "\n".join(page.get_text() for page in pdf)


def _extract_with_pdftotext(path: str) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", path, "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout
