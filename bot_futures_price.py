import logging
import json
import websockets
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from config import TOKEN_BOT
from db_utils.database import session, create_db
from db_utils.models import Task, PairToWatch


bot = Bot(token=TOKEN_BOT)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())
logging.basicConfig(level=logging.INFO)


async def get_futures_price():
    url = 'wss://stream.binance.com:9443/stream?streams='
    first_pair = 'btcusdt@aggTrade'
    watch_pairs = []
    param = session.query(PairToWatch).all()
    for elem in param:
        watch_pairs.append(elem.pair)
    async with websockets.connect(url+first_pair) as client:
        sub = {"method": "SUBSCRIBE", "params": watch_pairs, "id": 1}
        sub = json.dumps(sub)
        await client.send(str(sub))
        while True:
            lst_pairs = session.query(PairToWatch).all()
            if len(watch_pairs) != len(lst_pairs):
                unsub = {"method": "UNSUBSCRIBE", "params": watch_pairs, "id": 2}
                unsub = json.dumps(unsub)
                await client.send(str(unsub))
                watch_pairs = []
                for pair in lst_pairs:
                    watch_pairs.append(pair.pair)
                sub = {"method": "SUBSCRIBE", "params": watch_pairs, "id": 1}
                sub = json.dumps(sub)
                await client.send(str(sub))
            try:
                data = json.loads(await client.recv())['data']
                para_futures = session.query(Task).filter(Task.futures == data['s'].lower(), Task.done == False).all()
                for elem in para_futures:
                     if float(elem.price) == float(data['p']):
                         elem.done = True
                session.commit()
            except Exception:
                pass





if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(get_futures_price())

