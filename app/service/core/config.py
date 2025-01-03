import os
from typing import List

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    title: str = "Brightspace Middleware (Lite)"
    description: str = "Middleware between Brightspace and Migration scripts."
    cors_origins: List[str] = ["*"]
    app_prefix: str = os.environ.get("APP_PREFIX", "/")

    running_in_docker: bool = False
    debug: bool = os.environ.get("debug", True)
    log_level: str = "info"

    secret: bytes = os.environ.get("SECRET", os.urandom(24))
    version: str = ''

    # D2L #################################################
    d2l_id: str  = os.environ.get("D2L_ID", "")
    d2l_secret: str = os.environ.get("D2L_SECRET", "")
    d2l_url: str    = os.environ.get("D2L_URL", "")
    d2l_auth_url: str   = os.environ.get("D2L_AUTH_URL", "https://auth.brightspace.com/oauth2/auth")
    d2l_token_url: str  = os.environ.get("D2L_TOKEN_URL", "https://auth.brightspace.com/core/connect/token")
    d2l_redirect_uri: str  = os.environ.get("D2L_REDIRECT_URI", "")
    d2l_scope: str    = os.environ.get("D2L_SCOPE", "")
    d2l_call_allowed_hosts: str    = os.environ.get("D2L_CALL_ALLOWED_HOSTS", "0.0.0.0")

    # MySQL ###############################################
    sql_host: str  = os.environ.get("SQL_HOST", "localhost")
    sql_database: str    = os.environ.get("SQL_DATABASE", "brightspace")
    sql_user: str  = os.environ.get("SQL_USER", "brightspace")
    sql_pass: str  = os.environ.get("SQL_PASS", "brightspace")
    sql_port: int  = int(os.environ.get("SQL_PORT", 3306))

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.debug:
            self.log_level = 'debug'
        self.app_prefix = f'/{self.app_prefix}'.replace('//','/')
        self.load_version_from_file()

    def get_sql_alchemy_url(self):
        return f'mysql+pymysql://{self.sql_user}:{self.sql_pass}@{self.sql_host}/{self.sql_database}?charset=utf8mb4'

    def load_version_from_file(self):
        version_file_path = Path('VERSION')
        try:
            with open(version_file_path, 'r') as version_file:
                self.version = version_file.read().strip()
        except FileNotFoundError:
            print(f"Warning: Version file not found at '{version_file_path}'.")

    def get_dict(self):
        return {'title': self.title, 'description': self.description}

config = Config()
