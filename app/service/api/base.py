from api.v1 import users
from fastapi import APIRouter

router = APIRouter(prefix="/1.00")
router.include_router(users.router, prefix="/users", tags=["users"])
