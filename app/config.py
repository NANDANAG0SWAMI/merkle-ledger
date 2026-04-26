from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    operator_id: str
    operator_key: str
    topic_id: str
    anchor_topic_id: str
    anchor_batch_size: int = 10
    database_url: str = "sqlite+aiosqlite:///./hcs_logger.db"

    class Config:
        env_file = ".env"

settings = Settings()