from aiogram import Router
from .messages import router

def get_router() -> Router:
    shared_routers=Router()
    shared_routers.include_routers(
        router
    )
    return shared_routers