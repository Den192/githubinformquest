from typing import Union, Dict, Any
from os import getenv, name
from dotenv import load_dotenv
from pathlib import Path
if name == 'nt':
    load_dotenv(dotenv_path=Path(r'F:\Programming\gitInformNovemberQuestBot\.env'))
else:
    load_dotenv(dotenv_path=Path("/home/gitinformnovemberquestbot/.env"))
from aiogram.filters import BaseFilter
from aiogram.types import Message
from pymongo import MongoClient

mongo = MongoClient(getenv("MONGO_IP_PORT"),username=getenv("MONGO_USERNAME"),password=getenv("MONGO_PASSWORD"))
db=mongo.InformNovemberQuestBot
admin_collection = db.moderators

class HasModerRights(BaseFilter):
    async def __call__(self, message: Message) -> Union[bool, Dict[str, Any]]:
        # Если entities вообще нет, вернётся None,
        # в этом случае считаем, что это пустой список
        cursor = admin_collection.find({},{"_id":0,'UserId': 1})
        list_cursor = [result for result in cursor]
        editedcursor = [result["UserId"] for result in list_cursor]

        if message.from_user.id in editedcursor:
            return True
        else:
            return False