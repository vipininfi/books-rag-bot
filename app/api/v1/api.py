from fastapi import APIRouter

from app.api.v1.endpoints import books, search, auth, subscriptions

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(books.router, prefix="/books", tags=["books"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])