from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    db_url: str = Field(alias="DB_URL")
    api_key: str = Field(alias="API_KEY")


settings = Settings()
