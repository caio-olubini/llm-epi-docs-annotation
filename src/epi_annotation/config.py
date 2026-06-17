import glob as glob_module
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ValidationError


class InputCfg(BaseModel):
    data_dirs: list[str]
    glob: str = "*.pdf"


class PdfCfg(BaseModel):
    extractor: Literal["pymupdf", "pdftotext"] = "pymupdf"
    max_chars: int | None = None


class ModelCfg(BaseModel):
    name: str
    provider: Literal["openai", "anthropic", "google"]
    model_id: str
    temperature: float = 0.0
    max_tokens: int | None = None
    input_cost_per_1k: float | None = None
    output_cost_per_1k: float | None = None


class RunCfg(BaseModel):
    max_retries: int = 3
    concurrency: int = 4
    output_dir: str = "outputs/runs"


class PromptCfg(BaseModel):
    system_path: str


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
