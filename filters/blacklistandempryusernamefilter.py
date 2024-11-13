from typing import Callable, Dict, Any, Awaitable
from os import getenv, name
from dotenv import load_dotenv
from pathlib import Path
if name == 'nt':
    load_dotenv(dotenv_path=Path(r'F:\Programming\gitInformNovemberQuestBot\.env'))
else:
    load_dotenv(dotenv_path=Path("/home/gitinformnovemberquestbot/.env"))
from aiogram import BaseMiddleware
from aiogram.types import Message
from pymongo import MongoClient
mongo = MongoClient(getenv("MONGO_IP_PORT"),username=getenv("MONGO_USERNAME"),password=getenv("MONGO_PASSWORD"))
db = mongo.InformNovemberQuestBot
blacklist = db.blacklist

# Это будет outer-мидлварь на любые колбэки
class BlacklistMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        username = event.from_user.username
        if username is None:
            await event.answer("Для работы с ботом необходимо создать имя пользователя! Сделать это можно в настройках телеграмма", show_alert=True)
            return
        else:
            userid = event.from_user.id 
            cursor = blacklist.find({},{"_id":0,'UserId': 1})
            list_cursor = [result for result in cursor]
            editedcursor = [result["UserId"] for result in list_cursor]
            if userid in editedcursor:
                await event.answer("Вы были забанены!!!", show_alert=True)
                return
            else:
                return await handler(event,data)
