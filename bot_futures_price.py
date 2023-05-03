import logging
import json
import websockets
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from config import TOKEN_BOT
from db_utils.database import session, create_db
from db_utils.models import Task


bot = Bot(token=TOKEN_BOT)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())
logging.basicConfig(level=logging.INFO)


async def get_futures_price(current_task):
    url = f'wss://stream.binance.com:9443/stream?streams={current_task.futures}@aggTrade'
    async with websockets.connect(url) as client:
        while True:
            data = json.loads(await client.recv())['data']
            if data['p'] == current_task.price:
                session.query(Task).filter(Task.task_id == current_task.task_id).\
                    update(Task.done == True)
                session.commit()
                break
            print(f"{current_task.task_id}-{data['p']}")
        return data['p']


async def get_pending_tasks(last_task):
    tasks = session.query(Task).filter(Task.task_id > last_task).all()
    for task in tasks:
        if not task.done:
            tasks.append(task)

    return tasks, tasks[-1].task_id


async def process_tasks():
    last_task = 0
    while True:
        # Get the tasks that need to be processed
        tasks, last_task = await get_pending_tasks(last_task)

        # Process each task
        for task in tasks:
            await get_futures_price(task)

        # Wait for some time before checking for new tasks
        await asyncio.sleep(10)




# async def main():
#     last_task_id = 0
#     while True:
#         tasks = session.query(Task).filter(Task.task_id > last_task_id).all()
#         for task in tasks:
#             t1 = asyncio.create_task(get_futures_price(task.task_id, 'btcusdt'))
#             await t1
#             last_task_id = task.id
#         time.sleep(1)


if __name__ == '__main__':
    asyncio.run(process_tasks())
    # asyncio.run(main())

