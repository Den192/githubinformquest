from os import getenv, name
from dotenv import load_dotenv
from pathlib import Path
if name == 'nt':
    load_dotenv(dotenv_path=Path(r'F:\Programming\gitInformNovemberQuestBot\.env'))
else:
    load_dotenv(dotenv_path=Path("/home/gitinformnovemberquestbot/.env"))
from aiogram import Router, types, F
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from pymongo import MongoClient



moder_router = Router()
mongo = MongoClient(getenv("MONGO_IP_PORT"),username=getenv("MONGO_USERNAME"),password=getenv("MONGO_PASSWORD"))
db=mongo.InformNovemberQuestBot
user_id_collection = db.users
useranswers = db.useranswers

async def YesNoKeyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="Да")
    kb.button(text="Нет")
    kb.adjust(2)
    kb.row(types.KeyboardButton(text="Отмена"))
    return kb.as_markup(resize_keyboard = True)

async def KeyboardModer():
    kb = ReplyKeyboardBuilder()
    kb.button(text="Модерировать ответы")
    kb.row(types.KeyboardButton(text="Отменить"))
    return kb.as_markup(resize_keyboard = True)

class Moderation(StatesGroup):
    startmoder = State()

@moder_router.message(Command("moder"))
async def AdminAnswer(message: types.Message,state:FSMContext):
    await message.answer("!!!Режим Модератора!!!", reply_markup=await KeyboardModer())
    await state.clear()
@moder_router.message(F.text=="Модерировать ответы")
async def ModerationMessage(message:types.Message,state:FSMContext):
    useranswersmoder = list(useranswers.find({"moderchecked":None},{"_id":0,"userid":1,"challengenumber":1,"answer":1}))
    if len(useranswersmoder) == 0:
        await message.answer("Пока что все сообщения одмодерированы, для продолжения нажмите /start или /moder",reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return
    else:
        await state.set_state(Moderation.startmoder)
        await message.answer("Задание номер "+useranswersmoder[0]["challengenumber"]+"\nОтвет: "+useranswersmoder[0]["answer"],reply_markup=await YesNoKeyboard())
        await state.update_data(userid = useranswersmoder[0]["userid"],challengenumber = useranswersmoder[0]["challengenumber"])

@moder_router.message(Moderation.startmoder,F.text =="Отмена")
@moder_router.message(Moderation.startmoder,Command("cancel"))
@moder_router.message(Command("cancel"))
@moder_router.message(F.text.lower()=="отмена")
async def cancelmessage(message:types.Message,state:FSMContext):
    await message.answer("Проверка остановлена. Для продолжения выберите /add или /moder",reply_markup=types.ReplyKeyboardRemove())
    await state.clear()


@moder_router.message(Moderation.startmoder)
async def messagecheck(message:types.Message,state:FSMContext):
    if message.text=="Да":
        data = await state.get_data()
        index = next(i for i, challenge in enumerate(list(user_id_collection.find({"UserId":data["userid"]}, {"_id": 0, "challenges": 1}))[0]["challenges"]) if challenge[0] == data["challengenumber"])
        user_id_collection.update_one({"UserId":data["userid"]},{"$set":{"challenges."+str(index)+".1":True}})
        useranswers.update_one({"userid":data["userid"],"challengenumber":data["challengenumber"]},{"$set":{"moderchecked":True}})
        useranswersmodernew = list(useranswers.find({"moderchecked":None},{"_id":0,"userid":1,"challengenumber":1,"answer":1}))
        if len(useranswersmodernew)==0:
            await message.answer("Пока что все сообщения одмодерированы, для продолжения нажмите /start или /moder",reply_markup=types.ReplyKeyboardRemove())
            await state.clear()
            return
        else:
            await message.answer("Задание номер "+useranswersmodernew[0]["challengenumber"]+"\nОтвет: "+useranswersmodernew[0]["answer"],reply_markup=await YesNoKeyboard())
            await state.update_data(userid = useranswersmodernew[0]["userid"],challengenumber = useranswersmodernew[0]["challengenumber"])
    elif message.text=="Нет":
        data = await state.get_data()
        useranswers.update_one({"userid":data["userid"],"challengenumber":data["challengenumber"]},{"$set":{"moderchecked":False}})
        await message.answer("Задание зачтено не будет")
        useranswersmodernew = list(useranswers.find({"moderchecked":None},{"_id":0,"userid":1,"challengenumber":1,"answer":1}))
        if len(useranswersmodernew)==0:
            await message.answer("Пока что все сообщения одмодерированы, для продолжения нажмите /start или /moder",reply_markup=types.ReplyKeyboardRemove())
            await state.clear()
            return 
        else:
            await message.answer("Задание номер "+useranswersmodernew[0]["challengenumber"]+"\nОтвет: "+useranswersmodernew[0]["answer"],reply_markup=await YesNoKeyboard())
            await state.update_data(userid = useranswersmodernew[0]["userid"],challengenumber = useranswersmodernew[0]["challengenumber"])

