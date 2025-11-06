import os
import sys
import logging

from pathlib import Path

from typing import Any, List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s %(process)d %(levelname)-8s %(filename)s(%(lineno)d) %(message)s')

logging.getLogger("pyodata").setLevel(logging.WARN)

logger = logging.getLogger()

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='/run/secrets/passwords',
                                        env_file_encoding='utf-8',
                                        frozen=False,
                                        extra='ignore')

    title: str = "Brightspace Middleware (Lite)"
    description: str = "Middleware between Brightspace and Migration scripts."
    cors_origins: List[str] = ["*"]

    app_prefix: str = os.environ.get("APP_PREFIX", "/lite")
    debug: bool = os.environ.get("DEBUG", True)
    running_in_docker: bool = os.environ.get("RUNNING_IN_DOCKER", True)

    secret: bytes = Field(env='secret', description='secret key for the application')
    log_level: str = 'info'
    version: str = ''

    # D2L OAuth configuration
    D2L_ID: str  = Field(env='D2L_ID', description='D2L OAuth Client ID.')
    D2L_SECRET: str = Field(env='D2L_SECRET', description='D2L OAuth Client Secret.')
    D2L_URL: str    = Field(env='D2L_URL', description='D2L URL.')
    D2L_AUTH_URL: str   = Field(env='D2L_AUTH_URL', description='D2L OAuth URL.')
    D2L_TOKEN_URL: str  = Field(env='D2L_TOKEN_URL', description='D2L OAuth Fetch Token URL.')
    D2L_REDIRECT_URI: str  =Field(env='D2L_REDIRECT_URI', description='D2L OAuth redirect URL.')
    D2L_SCOPE: str    = Field(env='D2L_SCOPE', description='D2L OAuth Scope.')

    CALL_ALLOWED_HOSTS: str    = Field(env='CALL_ALLOWED_HOSTS', description='list of allowed hosts to call middleware from.')

    # MySQL database configuration
    SQL_HOST: str = Field(env='SQL_HOST', description='MySQL host address.')
    SQL_DATABASE: str = Field(env='SQL_DATABASE', description='MySQL database name.')
    SQL_USER: str = Field(env='SQL_USER', description='MySQL user name.')
    SQL_PASS: str = Field(env='SQL_PASS', description='MySQL user password.')
    SQL_PORT: int = Field(3306, env='SQL_PORT', description='MySQL port number.')
    SQL_CURSORCLASS: str = Field('DictCursor', env='SQL_CURSOR', description='MySQL cursor class to use.')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Save env_file if passed explicitly
        self._env_file_used = kwargs.get('_env_file', '/run/secrets/passwords')

        if self.debug:
            self.log_level = 'debug'

        self.app_prefix = f'/{self.app_prefix}'.replace('//','/')
        self.load_version_from_file()

    def get_sql_alchemy_url(self):
        return f'mysql+pymysql://{self.SQL_USER}:{self.SQL_PASS}@{self.SQL_HOST}/{self.SQL_DATABASE}?charset=utf8mb4'

    def load_version_from_file(self):
        version_file_path = Path('VERSION')
        try:
            with open(version_file_path, 'r') as version_file:
                self.version = version_file.read().strip()
        except FileNotFoundError:
            print(f"Warning: Version file not found at '{version_file_path}'.")

    def get_dict(self):
        return {'title': self.title, 'description': self.description}

settings = AppSettings()

def setup_logging(use_file: bool, logfile: str, debug: bool = False):
    # Clear existing handlers that basicConfig might have added
    logger.handlers.clear()

    # Pick log level based on debug flag
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s %(process)d %(levelname)-8s %(filename)s(%(lineno)d) %(message)s'
    )

    if use_file:
        fh = logging.FileHandler(logfile)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    else:
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(level)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
