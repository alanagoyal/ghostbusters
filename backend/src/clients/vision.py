"""Explicit cloud provider selection; existing installs default to Baseten."""

import os

from backend.src.clients.baseten_client import BasetenClient


def validate_openrouter_model(model):
    if not model or any(c.isspace() for c in model):
        raise ValueError("Choose an explicit OpenRouter vision model ID")
    # Free NVIDIA trial endpoints prohibit personal data, including faces.
    # Disallow automatic routing too: setup must review one explicit model.
    if (model.startswith("nvidia/") and model.endswith(":free")) or model in {
        "openrouter/free",
        "openrouter/auto",
    }:
        raise ValueError(
            "This endpoint is not approved for camera footage; "
            "see docs/CLOUD_PRIVACY.md"
        )


def request_options(env=None):
    env = os.environ if env is None else env
    if env.get("INFERENCE_PROVIDER", "baseten") == "openrouter":
        validate_openrouter_model(env.get("OPENROUTER_MODEL"))
        # Fail closed if no endpoint meets these constraints. Never retry without them.
        return {"provider": {"data_collection": "deny", "zdr": True}}
    return {}


def vision_settings(env=None):
    env = os.environ if env is None else env
    provider = env.get("INFERENCE_PROVIDER", "baseten")
    if provider == "baseten":
        return (
            env.get("BASETEN_API_KEY"),
            env.get("BASETEN_MODEL_URL"),
            env.get("BASETEN_MODEL", "gemma"),
            env.get("BASETEN_AUTH_SCHEME", "Api-Key"),
        )
    if provider == "openrouter":
        validate_openrouter_model(env.get("OPENROUTER_MODEL"))
        return (
            env.get("OPENROUTER_API_KEY"),
            "https://openrouter.ai/api/v1/chat/completions",
            env.get("OPENROUTER_MODEL"),
            "Bearer",
        )
    raise ValueError("Unsupported INFERENCE_PROVIDER")


def create_vision_client():
    key, endpoint, model, auth = vision_settings()
    if not all((key, endpoint, model)):
        raise ValueError("Missing cloud vision configuration")
    return BasetenClient(
        api_key=key,
        model_url=endpoint,
        model=model,
        auth_scheme=auth,
        request_options=request_options(),
    )
