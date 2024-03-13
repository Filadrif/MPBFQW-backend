from fastapi import APIRouter
from routers.auth import router as auth


router = APIRouter(prefix="/api")
router.include_router(auth, prefix="/user", tags=["Auth"])
