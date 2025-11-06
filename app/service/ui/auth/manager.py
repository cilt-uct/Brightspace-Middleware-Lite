# ui/auth/manager.py
from fastapi_login import LoginManager
from core.settings import settings
from db import crud, models

# manager = LoginManager(settings.secret, token_url="/login", use_cookie=True)
manager = LoginManager(
    settings.secret,
    token_url=f"{settings.app_prefix}/login",
    use_cookie=True,
    cookie_name="lite-access-token"  # or your custom name
    # you can optionally set use_header=False if you only want cookies
)

# somewhere after manager creation
@manager.user_loader()
def load_user(username: str):
    return crud.get_user(db, username=username)
