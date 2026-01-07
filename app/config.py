from pydantic import BaseSettings

class Settings(BaseSettings):
    whatsapp_token: str | None = None
    vector_db_path: str = "./vectorstore"
    openai_api_key: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
