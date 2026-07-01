import glob as glob_module
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ValidationError, model_validator


class InputCfg(BaseModel):
    data_dirs: list[str]
    glob: str = "*.pdf"


class PdfCfg(BaseModel):
    extractor: Literal["pymupdf", "pdftotext"] = "pymupdf"
    max_chars: int | None = None


class ModelCfg(BaseModel):
    name: str
    provider: Literal["openai", "anthropic", "google", "deepseek", "deepinfra"]
    model_id: str
    temperature: float = 0.0
    mode: str | None = None
    max_tokens: int | None = None
    input_cost_per_1k: float | None = None
    output_cost_per_1k: float | None = None


class RunCfg(BaseModel):
    max_retries: int = 3
    concurrency: int = 4
    output_dir: str = "outputs/runs"


class PromptCfg(BaseModel):
    """Named prompt versions plus which one this run uses.

    Versioning lets an experiment's output carry the exact prompt it was produced
    with (see fingerprint.py), so results stay comparable across prompt edits.
    """
    active: str
    versions: dict[str, str]

    @model_validator(mode="after")
    def active_must_be_a_known_version(self) -> "PromptCfg":
        if self.active not in self.versions:
            known = ", ".join(self.versions) or "(none)"
            raise ValueError(f"active prompt '{self.active}' not in versions: {known}")
        return self

    def active_path(self) -> str:
        return self.versions[self.active]


class Config(BaseModel):
    input: InputCfg
    pdf: PdfCfg
    models: list[ModelCfg]
    run: RunCfg
    prompt: PromptCfg


@dataclass
class Document:
    document_id: str
    source_dir: str
    path: str


def load_config(path: str = "config.yml") -> Config:
    try:
        with open(path) as f:
            raw = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        return Config.model_validate(raw)
    except ValidationError as exc:
        offending = exc.errors()[0]["loc"]
        field_path = ".".join(str(part) for part in offending)
        print(f"Config error at '{field_path}': {exc.errors()[0]['msg']}", file=sys.stderr)
        sys.exit(1)


def discover_documents(cfg: Config) -> list[Document]:
    documents = []
    for data_dir in cfg.input.data_dirs:
        pattern = str(Path(data_dir) / cfg.input.glob)
        for match in sorted(glob_module.glob(pattern)):
            path = Path(match)
            documents.append(Document(
                document_id=path.stem,
                source_dir=data_dir,
                path=str(path),
            ))
    return documents
