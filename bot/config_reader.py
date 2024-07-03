from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    bot_token: SecretStr
    
    debug_mode: bool
    
    minimum_players: int
    bank: int
    extent: int

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


config = Config()
