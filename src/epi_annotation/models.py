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
}


def build_client(model_cfg: ModelCfg) -> instructor.Instructor:
    import openai

    api_key = _require_api_key(model_cfg.provider)
    raw_client = openai.OpenAI(
        api_key=api_key,
        base_url=PROVIDER_BASE_URL[model_cfg.provider],
    )
    # JSON mode asks the model to emit the schema as JSON in the response body.
    # The default TOOLS (function-calling) mode is unreliable on Gemini's
    # OpenAI-compat endpoint for large nested schemas (MALFORMED_FUNCTION_CALL).
    return instructor.from_openai(raw_client, mode=instructor.Mode.JSON)


def _require_api_key(provider: str) -> str:
    env_var = PROVIDER_KEY_ENV[provider]
    key = os.environ.get(env_var)
    if not key:
        print(f"Missing credential for {provider}: set {env_var}", file=sys.stderr)
        sys.exit(1)
    return key
