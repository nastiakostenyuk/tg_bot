import asyncio
import logging
import requests
import json

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext

from settings import TOKEN_MAIN_BOT
from state import Cryptocurrency
from state import Task as state_task
from db_utils.database import session, create_db, delete_tables
from db_utils.models import Task, PairToWatch
from futures_price import get_futures_price


bot_main = Bot(token=TOKEN_MAIN_BOT)
dp_main = Dispatcher(bot_main, storage=MemoryStorage())

dp_main.middleware.setup(LoggingMiddleware())
logging.basicConfig(level=logging.INFO)

base = "https://data.binance.com"


async def get_done_task():
    para_futures = session.query(Task).filter(Task.done == True).all()
    if para_futures:
        for elem in para_futures:
            await bot_main.send_message(
                elem.user_id, f"Price reached {elem.futures} - {elem.price}"
            )
            session.delete(elem)
    session.commit()


@dp_main.message_handler(commands=["get_current_price"])
async def send_about(message: types.Message):
    await bot_main.send_message(message.from_user.id, "Write cryptocurrency")
    await Cryptocurrency.cryptocurrency.set()


@dp_main.message_handler(state=Cryptocurrency.cryptocurrency)
async def get_price(message: types.Message, state: FSMContext):
    path = "/api/v3/ticker/price"
    url = base + path
    symbol = message.text.upper()
    parameters = {"symbol": symbol}
    response = requests.get(url, params=parameters)

    if response.status_code == 200:
        js_response = json.loads(response.text)
        await message.reply(f"Current price: {js_response['price']}")
    else:
        print(response)
        await message.reply(f"Somethings went wrong")
    await state.finish()


@dp_main.message_handler(commands=["create_task"])
async def send_about(message: types.Message):
    await bot_main.send_message(message.from_user.id, "Write futures")
    await state_task.futures.set()


@dp_main.message_handler(state=state_task.futures)
async def get_futures(message: types.Message, state: FSMContext):
    path = f"/api/v3/exchangeInfo?symbol={message.text.upper()}"
    response = requests.get(base + path)
    if "code" in json.loads(response.text):
        await bot_main.send_message(message.from_user.id, "Bad futures")
        await state.finish()
    else:
        async with state.proxy() as data:
            data["futures"] = message.text
        await bot_main.send_message(message.from_user.id, "Write price")
        await state_task.price.set()


@dp_main.message_handler(state=state_task.price)
async def get_futures(message: types.Message, state: FSMContext):
    path = "/api/v3/ticker/price"
    url = base + path
    async with state.proxy() as data:
        data["price"] = float(message.text)
        symbol = data['futures'].upper()
        parameters = {"symbol": symbol}
        response = requests.get(url, params=parameters)
        js_response = json.loads(response.text)

        new_task = Task(
            user_id=message.from_user.id,
            futures=data["futures"].lower(),
            price=data["price"],
            last_price=float(js_response["price"]),
            is_long=float(js_response['price']) < data['price']
        )
        pairs = [elem.pair.split("@")[0] for elem in session.query(PairToWatch).all()]
        if (
            data["futures"].lower() not in pairs
            and data["futures"].lower() != "btcusdt"
        ):
            new_pair = PairToWatch(pair=data["futures"].lower() + "@aggTrade")
            session.add(new_pair)
        session.add(new_task)
        session.commit()
    await bot_main.send_message(message.from_user.id, "Done")
    await state.finish()


async def schedule():
    while True:
        await get_done_task()
        await asyncio.sleep(3)


async def main():
    task1 = asyncio.create_task(get_futures_price())
    task2 = asyncio.create_task(schedule())
    await asyncio.gather(task1, task2)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.create_task(executor.start_polling(dp_main, skip_updates=True))
    loop.run_forever()
