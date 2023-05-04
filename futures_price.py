import json
import websockets
import asyncio
import logging

from db_utils.database import session, create_db
from db_utils.models import Task, PairToWatch



async def get_futures_price():
    url = "wss://stream.binance.com:9443/stream?streams="
    first_pair = "btcusdt@aggTrade"
    watch_pairs = []
    param = session.query(PairToWatch).all()
    for elem in param:
        watch_pairs.append(elem.pair)
    async with websockets.connect(url + first_pair) as client:
        if watch_pairs:
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
                data = json.loads(await client.recv())["data"]
                para_futures = (
                    session.query(Task)
                    .filter(Task.futures == data["s"].lower(), Task.done == False)
                    .all()
                )
                last_price = float(data['p'])

                for elem in para_futures:
                    check_up = bool(float(elem.price) >= last_price)
                    check_down = bool(float(elem.price) <= last_price)
                    check = check_down if elem.is_long else check_up
                    if check:
                        elem.done = True
                session.commit()
            except Exception as exp:
                logging.error(exp)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(get_futures_price())
