import websockets
import asyncio
import json


async def get_futures_price(futures):
    url = f'wss://stream.binance.com:9443/stream?streams={futures}@aggTrade'
    async with websockets.connect(url) as client:
        while True:
            data = json.loads(await client.recv())['data']
            print(data['p'])


