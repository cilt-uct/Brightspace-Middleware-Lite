from api.v1 import users
# from apis.version1 import route_login
# from apis.version1 import route_users
from fastapi import APIRouter

router = APIRouter(prefix="/1.00")
router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(route_jobs.router, prefix="/jobs", tags=["jobs"])
# api_router.include_router(route_login.router, prefix="/login", tags=["login"])
