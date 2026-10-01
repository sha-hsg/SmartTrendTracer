"""litellm_config.yaml must name the provider for every deployment.

An unprefixed id ("claude-sonnet-5") makes LiteLLM infer the provider from
its model cost map. When the remote map cannot be fetched, the bundled map
does not know newer models and Router() raises at startup — on 2026-10-01
this took the whole backend down.
"""
from pathlib import Path

import yaml

CONFIG = Path(__file__).resolve().parents[1] / 'litellm_config.yaml'
PROVIDERS = {'anthropic', 'openai', 'gemini', 'xai'}


def test_every_deployment_names_its_provider():
    config = yaml.safe_load(CONFIG.read_text())
    bad = [
        f"{d.get('model_name')}: {d['litellm_params'].get('model')}"
        for d in config['model_list']
        if d['litellm_params'].get('model', '').split('/', 1)[0] not in PROVIDERS
    ]
    assert not bad, f'litellm_params.model needs a provider prefix: {bad}'
