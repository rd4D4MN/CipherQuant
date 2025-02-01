import pytest
from config.config_handler import ConfigHandler

def test_config_loading():
    config = ConfigHandler().config
    assert config.database['sqlite'].path == "./data/crypto.db"
    assert config.scraping['coingecko'].interval_seconds == 3600
    assert isinstance(config.models['lstm'].lookback_window, int)

def test_env_var_substitution(monkeypatch):
    monkeypatch.setenv("COINGECKO_API_KEY", "test_key")
    config = ConfigHandler().config
    assert config.apis['coingecko_api_key'] == "test_key"

