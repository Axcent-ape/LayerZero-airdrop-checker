import asyncio
import aiohttp
import aiofiles
import random
from fake_useragent import UserAgent
from loguru import logger
import sys


logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss.SS}</green> | <blue>{level}</blue> | <level>{message}</level>")


async def get_lines(path: str):
    async with aiofiles.open(path, 'r', encoding='utf-8') as file:
        lines = await file.readlines()
    return [line.strip() for line in lines]


class CheckEligible:
    def __init__(self, proxy: [str, None]):
        self.proxy = f"http://{proxy}" if proxy else None
        self.headers = {"User-Agent": UserAgent().random}

    async def check_eligible(self, address: str):
        async with aiohttp.ClientSession(trust_env=True, headers=self.headers) as session:
            try:
                resp = await session.get(f"https://www.layerzero.foundation/api/allocation/{address}", proxy=self.proxy)
                if resp.status != 200:
                    logger.warning(f"Not eligible {address}")
                    return False, 0.0

                resp_json = await resp.json()
                if resp_json.get('isEligible'):
                    drop = resp_json.get('zroAllocation', {}).get('asString', "0")
                    res_text = f"{address}:{drop}"
                    logger.success(f'Eligible for {drop} $ZRO {address}')

                    async with aiofiles.open('data/eligible.txt', 'a', encoding='utf-8') as f:
                        await f.write(f'{res_text}\n')
                    return True, float(drop)
                else:
                    logger.warning(f"Not eligible {address}")
                    return False, 0.0

            except Exception as e:
                logger.error(e)
                return False, 0.0


async def main():
    print("Автор чекера: https://t.me/ApeCryptor")

    thread_count = int(input("Введите кол-во потоков: "))

    addresses = await get_lines('data/accounts.txt')
    proxys = await get_lines('data/proxy.txt')

    tasks = []
    for address in addresses:
        proxy = random.choice(proxys) if proxys else None
        tasks.append(asyncio.create_task(CheckEligible(proxy=proxy).check_eligible(address=address)))

    results = []
    for i in range(0, len(tasks), thread_count):

        current_tasks = tasks[i:i + thread_count]
        results += await asyncio.gather(*current_tasks)

    eligible_wallets = 0
    drop = 0.0
    for result in results:
        if not result or not result[0]: continue
        drop += result[1]
        eligible_wallets += 1

    logger.info(f"\nTotal airdrop: {round(drop, 5)} $ZRO. Eligible wallets: {eligible_wallets}/{len(addresses)}")


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
