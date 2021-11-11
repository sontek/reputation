import os
from functools import lru_cache
from pydantic import BaseSettings


@lru_cache()
def get_settings():
    return Settings()


class Settings(BaseSettings):
    app_name: str = "baddies"

    @property
    def config(self):
        config = self.__dict__.get('_config')
        if config is None:
            REDIS_HOST: str = os.getenv("REDIS_HOST")
            REDIS_PORT: str = os.getenv("REDIS_PORT")
            REDIS_DATABASE: str = os.getenv("REDIS_DATABASE")
            API_ORIGIN: str = os.getenv("API_ORIGIN")
            config = {
                "REDIS_HOST": REDIS_HOST,
                "REDIS_PORT": REDIS_PORT,
                "REDIS_DATABASE": REDIS_DATABASE,
                "API_ORIGIN": API_ORIGIN,
            }
            self.__dict__['config'] = config

        return config
