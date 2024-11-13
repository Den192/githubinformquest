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
queststop = db.StoppingQuest
moders = db.moderators
admins = db.adminlist

async def flatlist(list):
    listtocreate = [result for result in list]
    editedlist = [result["UserId"] for result in listtocreate]
    return editedlist

# Это будет outer-мидлварь на любые колбэки
class StopQuestMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        StoppingQuest = list(queststop.find())
        
        if StoppingQuest[0]["queststopstatus"] is True:
            if event.from_user.id in await flatlist(moders.find({},{"_id":0,"UserId":1})) or await flatlist(admins.find({},{"_id":0,"UserId":1})):
                return await handler(event,data)
            else:
                await event.answer("К сожалению, квест закончился, ожидайте ответа!")
                return
        else:
            return await handler(event,data)
        userid = event.from_user.id 
        cursor = blacklist.find({},{"_id":0,'UserId': 1})
        list_cursor = [result for result in cursor]
        editedcursor = [result["UserId"] for result in list_cursor]
        if userid in editedcursor:
            await event.answer("Вы были забанены!!!", show_alert=True)
            return
        else:
            return await handler(event,data)
