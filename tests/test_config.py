import textwrap
from pathlib import Path

import pytest

from epi_annotation.config import Config, Document, discover_documents, load_config


def write_config(tmp_path: Path, content: str) -> str:
    path = tmp_path / "config.yml"
    path.write_text(textwrap.dedent(content))
    return str(path)


MINIMAL_CONFIG = """
    input:
      data_dirs: [.]
      glob: "*.pdf"
    pdf:
      extractor: pymupdf
    models:
      - name: gpt-4o
        provider: openai
        model_id: gpt-4o
    run:
      max_retries: 3
      concurrency: 4
      output_dir: outputs/runs
    prompt:
      active: v1
      versions:
        v1: prompts/system.md
"""


def test_load_config_returns_populated_config(tmp_path):
    path = write_config(tmp_path, MINIMAL_CONFIG)
    cfg = load_config(path)
    assert isinstance(cfg, Config)
    assert cfg.models[0].name == "gpt-4o"
    assert cfg.run.max_retries == 3
    assert cfg.pdf.extractor == "pymupdf"


def test_load_config_applies_defaults_when_fields_omitted(tmp_path):
    path = write_config(tmp_path, MINIMAL_CONFIG)
    cfg = load_config(path)
    assert cfg.run.concurrency == 4
    assert cfg.input.glob == "*.pdf"
    assert cfg.pdf.max_chars is None


def test_load_config_exits_on_bad_type(tmp_path):
    bad_config = MINIMAL_CONFIG.replace("max_retries: 3", "max_retries: not-a-number")
    path = write_config(tmp_path, bad_config)
    with pytest.raises(SystemExit):
        load_config(path)


def test_load_config_exits_when_file_missing(tmp_path):
    with pytest.raises(SystemExit):
        load_config(str(tmp_path / "nonexistent.yml"))


def test_load_config_exits_on_invalid_provider(tmp_path):
    bad_config = MINIMAL_CONFIG.replace("provider: openai", "provider: invalid_provider")
    path = write_config(tmp_path, bad_config)
    with pytest.raises(SystemExit):
        load_config(path)


def test_load_config_resolves_active_prompt_to_its_path(tmp_path):
    path = write_config(tmp_path, MINIMAL_CONFIG)
    cfg = load_config(path)
    assert cfg.prompt.active_path() == "prompts/system.md"


def test_load_config_exits_when_active_prompt_names_unknown_version(tmp_path):
    """An active version with no matching path would silently fall back to no
    prompt at run time; the config must reject it up front instead."""
    bad_config = MINIMAL_CONFIG.replace("active: v1", "active: v2")
    path = write_config(tmp_path, bad_config)
    with pytest.raises(SystemExit):
        load_config(path)


def test_discover_documents_finds_pdfs_in_data_dir(tmp_path):
    pdf_dir = tmp_path / "docs"
    pdf_dir.mkdir()
    (pdf_dir / "bulletin_01.pdf").write_bytes(b"%PDF-1.4")
    (pdf_dir / "bulletin_02.pdf").write_bytes(b"%PDF-1.4")
    (pdf_dir / "readme.txt").write_text("not a pdf")

    config_path = write_config(tmp_path, MINIMAL_CONFIG.replace("data_dirs: [.]", f"data_dirs: [{pdf_dir}]"))
    cfg = load_config(config_path)

    docs = discover_documents(cfg)
    assert len(docs) == 2
    assert all(isinstance(d, Document) for d in docs)
    assert all(d.path.endswith(".pdf") for d in docs)


def test_discover_documents_returns_empty_when_no_pdfs(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    config_path = write_config(tmp_path, MINIMAL_CONFIG.replace("data_dirs: [.]", f"data_dirs: [{empty_dir}]"))
    cfg = load_config(config_path)

    docs = discover_documents(cfg)
    assert docs == []


def test_discover_documents_finds_pdfs_in_real_golden_standard_base():
    """Smoke test: real data dir must contain at least one PDF."""
    try:
        cfg = load_config("config.yml")
    except SystemExit:
        pytest.skip("config.yml not available or invalid")

    docs = discover_documents(cfg)
    assert len(docs) > 0, "Expected at least one PDF in data/raw/golden_standard_base"
