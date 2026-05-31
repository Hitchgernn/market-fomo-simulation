import os
from unittest.mock import patch

from backend.api.server import SimulationConfig, create_model, _chat_status
from backend.llm.rotator import AgentChatRotator


def test_openrouter_provider_uses_configured_model():
    env = {
        "CHAT_PROVIDER": "openrouter",
        "OPENROUTER_API_KEY": "test-key",
        "OPENROUTER_MODEL": "meta-llama/llama-3.2-3b-instruct:free",
    }
    with patch.dict(os.environ, env, clear=True):
        model = create_model(SimulationConfig())

    assert model.chat_rotator.provider == "openrouter"
    assert model.chat_rotator.model_name == "meta-llama/llama-3.2-3b-instruct:free"


def test_ollama_provider_uses_local_model_config():
    env = {
        "CHAT_PROVIDER": "ollama",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "qwen3.5:4b",
    }
    with patch.dict(os.environ, env, clear=True):
        model = create_model(SimulationConfig())

    assert model.chat_rotator.provider == "ollama"
    assert model.chat_rotator.model_name == "qwen3.5:4b"
    assert model.chat_rotator.base_url == "http://localhost:11434"


def test_chat_status_reports_enabled_provider_model_and_last_error():
    rotator = AgentChatRotator(api_keys=["x"], provider="gemini", model_name="gemini-test")
    rotator.last_error = "boom"

    status = _chat_status(rotator)

    assert status == {
        "enabled": True,
        "provider": "gemini",
        "model": "gemini-test",
        "lastError": "boom",
    }


def test_chat_status_reports_disabled_without_rotator():
    assert _chat_status(None) == {
        "enabled": False,
        "provider": None,
        "model": None,
        "lastError": None,
    }
