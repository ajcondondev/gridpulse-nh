from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    eia_api_key: str = ""
    noaa_token: str = ""
    nrel_api_key: str = "DEMO_KEY"
    api_data_dir: str = "../../data"

    @property
    def data_dir(self) -> Path:
        return Path(self.api_data_dir).resolve()

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def cleaned_dir(self) -> Path:
        return self.data_dir / "cleaned"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"

    @property
    def metadata_dir(self) -> Path:
        return self.data_dir / "metadata"


settings = Settings()
