from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    tg_token: str        = Field(..., env='TG_TOKEN')
    mongo_dsn: str       = Field(..., env='MONGO_DSN')
    log_level: str       = Field('INFO', env='LOG_LEVEL')

    class Config:
        env_file = '.env'

settings = Settings()
