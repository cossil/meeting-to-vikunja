import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    VIKUNJA_API_TOKEN: str
    VIKUNJA_API_URL: str

    class Config:
        env_file = "../.env"
        extra = "ignore" 

settings = Settings()
