import os
from pathlib import Path
from typing import Dict, Any
import yaml
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

class DatabaseConfig(BaseModel):
    path: str
    tables: Dict[str, str]

class ScrapingConfig(BaseModel):
    base_url: str
    endpoints: Dict[str, str]
    params: Dict[str, Any]
    interval_seconds: int
    max_retries: int
    user_agents: list[str]

class ModelConfig(BaseModel):
    lookback_window: int
    epochs: int
    batch_size: int
    train_test_split: float

class Config(BaseModel):
    scraping: Dict[str, ScrapingConfig]
    database: Dict[str, DatabaseConfig]
    models: Dict[str, ModelConfig]
    apis: Dict[str, str]

class ConfigHandler:
    def __init__(self):
        self.config_path = Path(__file__).parent / "config.yaml"
        self.config = self._load_config()

    def _load_config(self) -> Config:
        with open(self.config_path) as f:
            raw_config = yaml.safe_load(f)
            # Replace environment variables
            for key, value in raw_config['apis'].items():
                if isinstance(value, str) and value.startswith('${'):
                    env_var = value[2:-1]
                    raw_config['apis'][key] = os.getenv(env_var)
            return Config(**raw_config)

    def get(self, section: str) -> Any:
        return self.config.dict().get(section)