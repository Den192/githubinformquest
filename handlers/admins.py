from os import getenv, name
from dotenv import load_dotenv
from pathlib import Path
if name == 'nt':
    load_dotenv(dotenv_path=Path(r'F:\Programming\gitInformNovemberQuestBot\.env'))
else:
    load_dotenv(dotenv_path=Path("/home/gitinformnovemberquestbot/.env"))
from bson import ObjectId
from aiogram import Router, types, F, Bot
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from pymongo import MongoClient

admin_router = Router()
bot = Bot(token=getenv("TG_TOKEN"))
mongo = MongoClient(getenv("MONGO_IP_PORT"),username=getenv("MONGO_USERNAME"),password=getenv("MONGO_PASSWORD"))
db=mongo.InformNovemberQuestBot
user_id_collection = db.users
challenges = db.challenges
blacklist = db.blacklist
stopquest = db.StoppingQuest
useranswersdb = db.useranswers

class addchallengestate(StatesGroup):
    startaddchallenge = State()
    startaddhint = State()
    startaddanswer = State()
class banstate(StatesGroup):
    startban=State()
    endban=State()
class unbanstate(StatesGroup):
    startunban=State()
class endqueststate(StatesGroup):
    startendquest = State()
class userliststate(StatesGroup):
    startuserlist = State()
class answerliststate(StatesGroup):
    startanswerlist = State() 
class messagetoall(StatesGroup):
    startmessage = State()


async def KeyboardMain():
    Keyboard = ReplyKeyboardBuilder()
    Keyboard.button(text="Добавить задание"),
    Keyboard.button(text="Забанить"),
    Keyboard.button(text="Разбанить"),
    Keyboard.button(text="Пользователи"),
    Keyboard.adjust(4)
    Keyboard.row(types.KeyboardButton(text="Ответы пользователей"))
    Keyboard.row(types.KeyboardButton(text="Сообщение всем пользователям"))
    Keyboard.row(types.KeyboardButton(text="Подвести итоги"))
    Keyboard.row(types.KeyboardButton(text="Отменить"))
    return Keyboard.as_markup(resize_keyboard=True)

async def keyboardBuilder(BanUnban):
    builder = ReplyKeyboardBuilder()
    if BanUnban == True:
        cursor = user_id_collection.find({},{"_id":0,'username': 1})
    elif BanUnban == False:
        cursor = blacklist.find({},{"_id":0,'username': 1})
    list_cursor = [result for result in cursor]
    editedcursor = [result["username"] for result in list_cursor]
    for i in range(0,len(editedcursor)):
        builder.button(text=f"{editedcursor[i]}")
    builder.adjust(3)
    builder.row(types.KeyboardButton(text="Отменить"))
    return builder.as_markup(resize_keyboard=True)

async def YesNoKeyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="Да")
    kb.button(text="Нет")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard = True)

async def buttonnumber():
    pages = user_id_collection.count_documents({}) // 5 
    if user_id_collection.count_documents({}) % 5 != 0:
        pages += 1
    return pages

async def answernumber():
    pages = useranswersdb.count_documents({}) // 5 
    if useranswersdb.count_documents({}) % 5 != 0:
        pages += 1
    return pages

async def userkeyboard():
    builder = ReplyKeyboardBuilder()
    button = await buttonnumber()
    for i in range(1,button+1):
        builder.button(text=f"{i}")
    builder.adjust(5)
    builder.row(types.KeyboardButton(text="Выход из просмотра"))
    return builder.as_markup(resize_keyboard=True)

async def answerkeyboard():
    builder = ReplyKeyboardBuilder()
    button = await answernumber()
    for i in range(1,button+1):
        builder.button(text=f"{i}")
    builder.adjust(5)
    builder.row(types.KeyboardButton(text="Выход из просмотра"))
    return builder.as_markup(resize_keyboard=True)

@admin_router.message(Command("admin"))
async def AdminAnswer(message: types.Message,state:FSMContext):
    await message.answer("!!!Режим Администратора!!!", reply_markup=await KeyboardMain())
    await state.clear()
@admin_router.message(F.text=="Добавить задание")
async def addchallenge(message:types.Message,state:FSMContext):
    cursor = challenges.find({},{"_id":0,'challengenumber': 1})
    list_cursor = [result for result in cursor]
    editedcursor = [result["challengenumber"] for result in list_cursor]
    listToStr = ' '.join([str(elem) for elem in editedcursor])
    await message.answer("Введите номер задания, в данный момент существуют: "+listToStr,reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(addchallengestate.startaddchallenge)
    del cursor,list_cursor,editedcursor,listToStr
@admin_router.message(addchallengestate.startaddchallenge,F.text!="/cancel")
async def textchallenge(message:types.Message,state:FSMContext):
    await message.answer("Введите подсказку для пользователей")
    await state.set_state(addchallengestate.startaddhint)
    await state.update_data(challengenumber = message.text)
@admin_router.message(addchallengestate.startaddhint,F.text!="/cancel")
async def answerchallenge(message:types.Message,state:FSMContext):
    await state.update_data(hint = message.text)
    await message.answer("Введите ответ на задание")
    await state.set_state(addchallengestate.startaddanswer)
@admin_router.message(addchallengestate.startaddanswer,F.text!="/cancel")
async def hintchallenge(message:types.Message,state:FSMContext):
    data = await state.get_data()
    user_id_collection.update_many({},{"$push": {"challenges": [data["challengenumber"], False]}})
    challenges.insert_one({"challengenumber":data["challengenumber"],"hint":data["hint"],"answer":message.text})
    await message.answer("Задание под номером "+data["challengenumber"]+" успешно добавлено!\nДля продолжения нажмите /admin или /start")
    await state.clear()


@admin_router.message(F.text.lower()=="забанить")
async def BanUser(message:types.Message,state:FSMContext):
    await state.set_state(banstate.startban)
    await message.answer("Выберите пользователя для бана", reply_markup=await keyboardBuilder(True))
@admin_router.message(banstate.startban, F.text != '/cancel',F.text.lower()!="отменить")
async def UserIdBan(message: types.Message,state:FSMContext):
    useridindb = list(user_id_collection.find({'username': message.text}))
    if len(useridindb)==0:
        await message.answer("Такой пользователь не существует!!")
        return
    result = blacklist.find_one({"userid":useridindb[0]["UserId"]})
    if result is None:
        blacklist.insert_one({"UserId":useridindb[0]["UserId"],"username":message.text})
        await message.answer(f"Пользователь {message.text} был забанен.",reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer(f"Пользователь {message.text} уже забанен!!!",reply_markup=types.ReplyKeyboardRemove())
    await message.answer("Для дальнейшей работы, нажмите /admin или /start")
    await state.clear()
    del result,useridindb
@admin_router.message(F.text.lower()=="разбанить")
async def Unban(message:types.Message,state:FSMContext):
    await state.set_state(unbanstate.startunban)
    await message.answer("Выберите пользователя для разбана", reply_markup=await keyboardBuilder(False))
@admin_router.message(unbanstate.startunban,F.text != '/cancel',F.text.lower()!="отменить")
async def NextUnban(message:types.Message,state:FSMContext):
    useridindb = list(blacklist.find({'username': message.text}))
    if len(useridindb)==0:
        await message.answer("Пользователя нет в списке!!")
        await state.clear()
        return
    result = blacklist.find_one({"UserId":useridindb[0]["UserId"]})
    if result is not None:
        blacklist.delete_one({"UserId":useridindb[0]["UserId"]})
    await message.answer(f"Пользователь {message.text} был разбанен.",reply_markup=types.ReplyKeyboardRemove())
    await message.answer("Для дальнейшей работы, нажмите /admin или /start")
    await state.clear()
    del result,useridindb

@admin_router.message(F.text.lower()=="пользователи")
async def Messagehistory(message: types.Message, state:FSMContext):
    await state.set_state(userliststate.startuserlist)
    await message.answer("Список пользователей",reply_markup=await userkeyboard())
    await message.answer("Выберите страницу из списка ниже")

@admin_router.message(userliststate.startuserlist,F.text!="Выход из просмотра")
async def MessageHistoryPages(message:types.Message):
    await message.answer("Страница: "+message.text,reply_markup=await userkeyboard())
    pagenumber = int(message.text)
    messagetext = list(user_id_collection.find({},{"_id":0}).skip(5*(pagenumber-1)).limit(5))
    if len(messagetext)<5:
        rang=len(messagetext)
    else: 
        rang=5
    for i in range(0,rang):
        useranswer = list(useranswersdb.find({"userid":messagetext[i]["UserId"],"moderchecked":True},{"_id":0,"challengenumber":1}))
        useranswerflat = list()
        for n in range(0,len(useranswer)):
            useranswerflat.extend(useranswer[n]["challengenumber"])
        myresults = [messagetext[i]["UserId"],messagetext[i]["username"],messagetext[i]["registrationDate"],messagetext[i]["FIO"],messagetext[i]["GroupNumber"]]
        await message.answer("UserID пользователя: "+str(myresults[0])+"\nНик пользователя: @"+myresults[1]+"\nДата регистрации(дата/время): "+myresults[2]+"\nФИО пользователя: "+str(myresults[3])+"\nНомер группы: "+myresults[4]+"\nПравильно выполненные задания: "+' '.join(useranswerflat))
        del myresults,useranswerflat
    del messagetext,pagenumber


@admin_router.message(F.text.lower()=="ответы пользователей")
async def Messagehistory(message: types.Message, state:FSMContext):
    await state.set_state(answerliststate.startanswerlist)
    await message.answer("Список ответов",reply_markup=await answerkeyboard())
    await message.answer("Выберите страницу из списка ниже")

@admin_router.message(answerliststate.startanswerlist,F.text!="Выход из просмотра")
async def MessageHistoryPages(message:types.Message):
    await message.answer("Страница: "+message.text,reply_markup=await answerkeyboard())
    pagenumber = int(message.text)
    messagetext = list(useranswersdb.find({},{"_id":0}).skip(5*(pagenumber-1)).limit(5))
    if len(messagetext)<5:
        rang=len(messagetext)
    else: 
        rang=5
    for i in range(0,rang):
        myresults = [messagetext[i]["userid"],messagetext[i]["username"],messagetext[i]["challengenumber"],messagetext[i]["answer"],messagetext[i]["moderchecked"],messagetext[i]["answertime"]]
        await message.answer("UserID пользователя: "+str(myresults[0])+"\nНик пользователя: @"+myresults[1]+"\nНомер задания: "+myresults[2]+"\nОтвет пользователя: "+str(myresults[3])+"\nРезультат проверки: "+str(myresults[4])+"\nВремя ответа: "+myresults[5])
        del myresults
    del messagetext,pagenumber




@admin_router.message(F.text=="Подвести итоги")
async def StopQuest(message:types.Message,state:FSMContext):
    await message.answer("Вы выбрали кнопку подвести итоги, после выбора Да, квест будет остановлен и это действие отменить невозможно.\nВы точно уверены в этом действии?",reply_markup=await YesNoKeyboard())
    await state.set_state(endqueststate.startendquest)
@admin_router.message(endqueststate.startendquest,F.text=="Да")
async def CreatingResults(message:types.Message,state:FSMContext):
    stopquest.update_one({"_id":ObjectId("66eb677990934756c5320fc8")},{"$set":{"queststopstatus":True}})
    results = list()
    users = user_id_collection.find({})
    for user in users:
        user_answers = useranswersdb.find({"userid": user["UserId"]})
        answer_times = []
        for answer in user_answers:
            challenge_number = answer["challengenumber"]
            answer_time = answer["answertime"]
            answer_times.append({"challengenumber": challenge_number, "answertime": answer_time})
        all_answered = True
        for challenge in challenges.find({}):
            challenge_number = challenge["challengenumber"]
            if not useranswersdb.find_one({"userid": user["UserId"], "challengenumber": challenge_number}):
                all_answered = False
                break
        if all_answered:
            all_moderated = True
            for answer in user_answers:
                if not answer["moderchecked"]:
                    all_moderated = False
                    break
            if all_moderated:
                results.append([user["UserId"], user["username"], user["registrationDate"], user["FIO"], user["GroupNumber"], answer_times])
    chalnum = list()
    anstime = list()
    for i in range(0,len(results)):
        for n in range(0,len(results[i][5])):
            chalnum.append(results[i][5][n]["challengenumber"])
            anstime.append(results[i][5][n]["answertime"])
        await message.answer("Победитель\nUserID: "+str(results[i][0])+"\nНикнейм: @"+results[i][1]+"\nВремя регистрации: "+results[i][2]+"\nФИО: "+results[i][3]+"\nНомер группы: "+results[i][4]+"\n"+"Ответы на задания: \n"+"\n".join([" - ".join([str(item1),str(item2)]) for item1, item2 in zip(chalnum,anstime)]))
        chalnum.clear()
        anstime.clear()
    del all_answered,all_moderated,anstime,answer,answer_time,answer_times,challenge,challenge_number,chalnum,results,user,user_answers,users,i,n
    await message.answer("Квест был остановлен, работать с ботом могут лишь администраторы и модераторы\nВыберите действие", reply_markup=await KeyboardMain())
    await state.clear()
    
@admin_router.message(F.text=="Сообщение всем пользователям")
async def MessageToAll(message: types.Message,state:FSMContext):
    await message.answer("Введенное сообщение будет отправлено всем пользователям\nВведите сообщение",reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(messagetoall.startmessage)
@admin_router.message(messagetoall.startmessage,F.text!="/cancel" or F.text!="Отменить")
async def sendmessagetoall(message: types.Message,state:FSMContext):
    userlist = list(user_id_collection.find({},{"_id":0,"UserId":1}))
    list_cursor = [result for result in userlist]
    editedcursor = [result["UserId"] for result in list_cursor]
    for i in range(0,len(editedcursor)):
        await bot.send_message(chat_id=editedcursor[i],text=message.text)
    await message.answer("Сообщение было отправлено! Для дальнейшей работы нажмите /start или /admin")
    await state.clear()

@admin_router.message(addchallengestate.startaddhint,Command("cancel"))
@admin_router.message(addchallengestate.startaddchallenge,Command("cancel"))
@admin_router.message(banstate.startban,F.text.lower()==("отменить"))
@admin_router.message(banstate.endban,F.text.lower()==("отменить"))
@admin_router.message(unbanstate.startunban,F.text.lower()==("отменить"))
@admin_router.message(endqueststate.startendquest,F.text=="Нет")
@admin_router.message(messagetoall.startmessage,F.text=="/cancel" or F.text=="Отменить")
@admin_router.message(userliststate.startuserlist,F.text==("Выход из просмотра"))
@admin_router.message(answerliststate.startanswerlist,F.text==("Выход из просмотра"))
async def PhotoCancel(message: types.Message, state:FSMContext):
    await message.answer("Действие отменено, начните сначала",reply_markup=types.ReplyKeyboardRemove())
    await message.answer(text="Выберите действие",reply_markup=await KeyboardMain())
    await state.clear()

@admin_router.message(F.text=="Отменить")
async def Exit(message:types.Message):
    await message.answer("Для дальнейшей работы нажмите /start или /admin", reply_markup=types.ReplyKeyboardRemove())