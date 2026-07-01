import os
import sys

import instructor
from dotenv import load_dotenv

from epi_annotation.config import ModelCfg

load_dotenv()

PROVIDER_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "deepseek": "DEEPSEEK_KEY",
    "deepinfra": "DEEPINFRA_KEY",
}

# Anthropic and Google both expose OpenAI-compatible endpoints, so every provider
# is reached through a single openai.OpenAI client with the base_url swapped. This
# keeps one code path and avoids each native SDK's idiosyncrasies (e.g. Gemini's
# old SDK rejects temperature= and bakes model= into the client). openai uses its
# own default base_url when None is passed.
PROVIDER_BASE_URL = {
    "openai": None,
    "anthropic": "https://api.anthropic.com/v1/",
    "google": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "deepseek": "https://api.deepseek.com",
    "deepinfra": "https://api.deepinfra.com/v1/openai/"
}

def build_client(model_cfg: ModelCfg) -> instructor.Instructor:
    import openai

    if model_cfg.mode is None:
        print(f"Model '{model_cfg.name}' has no 'mode' set in config.yml.", file=sys.stderr)
        sys.exit(1)

    api_key = _require_api_key(model_cfg.provider)
    raw_client = openai.OpenAI(
        api_key=api_key,
        base_url=PROVIDER_BASE_URL[model_cfg.provider],
    )

    try:
        mode = instructor.Mode(model_cfg.mode)
    except ValueError:
        valid = [m.value for m in instructor.Mode]
        print(
            f"Unknown instructor mode '{model_cfg.mode}' for model '{model_cfg.name}'. "
            f"Valid values: {valid}",
            file=sys.stderr,
        )
        sys.exit(1)

    return instructor.from_openai(raw_client, mode=mode)

def _require_api_key(provider: str) -> str:
    env_var = PROVIDER_KEY_ENV[provider]
    key = os.environ.get(env_var)
    if not key:
        print(f"Missing credential for {provider}: set {env_var}", file=sys.stderr)
        sys.exit(1)
    return key
