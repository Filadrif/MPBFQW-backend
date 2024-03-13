from fastapi import APIRouter
from routers.auth import router as auth
from routers.course import router as course


router = APIRouter(prefix="/api")
router.include_router(auth, prefix="/user", tags=["Auth"])
router.include_router(course, prefix="/course", tags=["Course"])
