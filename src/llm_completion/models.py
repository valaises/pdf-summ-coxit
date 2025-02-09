import json
import os

from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path

from core.logger import error


__all__ = ["ModelInfo", "get_model_list"]


@dataclass
class ModelProviderInfo:
    name: str
    env: Optional[str]

@dataclass
class ModelInfo:
    name: str
    provider: str
    resolve_as: str
    context_window: int
    max_output_tokens: int
    price_points_input: int
    price_points_output: int
    tokens_per_minute: Optional[int]
    request_per_minute: Optional[int]


def _models_info(base_dir: Path) -> List[ModelInfo]:
    models_file = base_dir.joinpath("assets").joinpath("model_list.json")
    assert models_file.is_file(), f"model_list.json not found at {models_file}"

    models_json = json.loads(models_file.read_text())

    return [
        ModelInfo(
            name=model_name,
            provider=model_info["provider"],
            resolve_as=model_info["resolve_as"],
            context_window=model_info["context_window"],
            max_output_tokens=model_info["max_output_tokens"],
            price_points_input=model_info["price_points_input"],
            price_points_output=model_info["price_points_output"],
            tokens_per_minute=model_info.get("tpm"),
            request_per_minute=model_info.get("rpm"),
        )
        for model_data in models_json
        for model_name, model_info in model_data.items()
    ]

def get_model_providers(base_dir: Path) -> List[ModelProviderInfo]:
    providers_file = base_dir.joinpath("assets").joinpath("model_providers.json")
    assert providers_file.is_file(), f"model_providers.json not found at {providers_file}"

    providers_json = json.loads(providers_file.read_text())

    return [
        ModelProviderInfo(
            name=provider_name,
            env=provider_info.get("env"),
        )
        for provider_data in providers_json
        for provider_name, provider_info in provider_data.items()
    ]

def get_model_list(base_dir: Path) -> List[ModelInfo]:
    all_models = _models_info(base_dir)
    providers = get_model_providers(base_dir)

    filtered_models = []
    for m in all_models:
        if not (p := next((p for p in providers if p.name == m.provider), None)):
            error(f"model {m.name}: provider {m.provider} not found. SKIPPING")
            continue

        if p.env and not os.environ.get(p.env):
            error(f"model {m.name}: provider {m.provider} env {p.env} not set. SKIPPING")
            continue

        filtered_models.append(m)

    return filtered_models
