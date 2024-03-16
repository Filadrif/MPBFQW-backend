from fastapi import APIRouter
from routers.auth import router as auth
from routers.course import router as course
from routers.student import router as student
from routers.message import router as message


router = APIRouter(prefix="/api")
router.include_router(auth, prefix="/user", tags=["Auth"])
router.include_router(course, prefix="/course", tags=["Course"])
router.include_router(message, prefix="/course", tags=["Info channel"])
router.include_router(student, prefix="/student", tags=["Student"])
