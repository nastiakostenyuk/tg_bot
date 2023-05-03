import websockets
import asyncio
import json


async def get_futures_price(futures):
    url = f'wss://stream.binance.com:9443/stream?streams={futures}@aggTrade'
    async with websockets.connect(url) as client:
        while True:
            data = json.loads(await client.recv())['data']
            print(data['p'])


async def main():
    t1 = asyncio.create_task(get_futures_price('ethusdt'))
    t2 = asyncio.create_task(get_futures_price('btcusdt'))
    await t1
    await t2


if __name__ == '__main__':
    asyncio.run(main())
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(get_futures_price('ethusdt'))
