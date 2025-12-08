import configparser
import os
import re

basedir = os.path.abspath(os.path.dirname(__file__))

class MyConfigParser(configparser.RawConfigParser):
    def get(self, section, option, *args, **kwargs):
        val = super().get(section, option, *args, **kwargs)
        if val is None:
            return None
        if isinstance(val, str): # if it is a string then strip quotes if they exist
            return val.strip('"').strip("'")
        return val

class Config:

    STATIC_FOLDER = f'{os.getenv('APP_FOLDER')}/project/static'
    DEBUG = os.environ.get('DEBUG', 'false').lower() in ('true', '1', 't')
    RUNNING_IN_DOCKER = os.environ.get('RUNNING_IN_DOCKER', False)

    APP_PREFIX = os.environ.get('APP_PREFIX', '/lite')
    APPLICATION_ROOT = APP_PREFIX
    SCRIPT_NAME = APP_PREFIX

    SERVER_TYPE = os.environ.get('ENV', 'dev')

    SCHEDULER_API_ENABLED = True

    VERSION = ''
    with open('VERSION') as file:
        VERSION = file.read().rstrip()

    # Load secrets from passwords.txt
    secrets_file = '/run/secrets/passwords'
    if os.path.isfile(secrets_file):
        with open(secrets_file) as f:
            content = f.read()

        content = '[secrets]\n' + content
        parser = MyConfigParser()
        parser.read_string(content)

        secrets = parser['secrets']
        # for key, value in parser['secrets'].items():
            # setattr(Config, key.upper(), value)

        SECRET_KEY = secrets.get('SECRET', os.urandom(24))

        CORS_ORIGINS = secrets.get('CORS_ORIGINS', 'https://amathuba.uct.ac.za,https://ucttest.brightspace.com').split(',')

        CLIENT_ID = secrets.get('D2L_ID')
        CLIENT_SECRET = secrets.get('D2L_SECRET')
        BASE_URL = secrets.get('D2L_URL')
        REDIRECT_URI = secrets.get('D2L_REDIRECT_URI')
        AUTHORIZATION_BASE_URL = secrets.get('D2L_AUTH_URL')
        TOKEN_URL = secrets.get('D2L_TOKEN_URL')
        SCOPE = secrets.get('D2L_SCOPE')

        CALL_ALLOWED_HOST = secrets.get('CALL_ALLOWED_HOSTS', '').split(',')

        MYSQL_HOST = secrets.get('SQL_HOST', 'localhost')
        MYSQL_DB   = secrets.get('SQL_DATABASE', 'brightspace')
        MYSQL_USER = secrets.get('SQL_USER', 'brightspace')
        MYSQL_PASSWORD = secrets.get('SQL_PASS', 'brightspace')
        MYSQL_PORT = int(secrets.get('SQL_PORT', 3306))
        MYSQL_CURSORCLASS = 'DictCursor'
        # https://mysqlclient.readthedocs.io/user_guide.html#functions-and-attributes
        # MYSQL_CUSTOM_OPTIONS = {"ssl": {"ca": "/path/to/ca-file"}}

        SQLALCHEMY_DATABASE_URI = f'mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
        SQLALCHEMY_TRACK_MODIFICATIONS = False

        srv = secrets.get('D2L_REDIRECT_URI', None)
        srv_group = re.search(r'//([A-Za-z]{3}).*([A-Za-z]{3}\d{3})', srv)
        if srv_group:
            srv = srv_group.group(1) + srv_group.group(2)
        else:
            srv = 'lite'
