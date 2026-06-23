import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PromptFingerprint:
    """Identifies which prompt produced an annotation.

    `version` is the human-chosen name from config; `sha256` is taken from the
    prompt's content so that editing a file in place — without renaming the
    version — is still detectable when comparing runs.
    """
    version: str
    path: str
    sha256: str


def fingerprint_prompt(version: str, path: str) -> PromptFingerprint:
    content = Path(path).read_bytes()
    return PromptFingerprint(
        version=version,
        path=path,
        sha256=hashlib.sha256(content).hexdigest(),
    )
