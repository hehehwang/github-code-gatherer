from configparser import ConfigParser

from typing import List
from time import sleep
from common import *

import requests
from aiohttp import ClientSession, BasicAuth
import asyncio
from pprint import pprint
from datetime import datetime

config = ConfigParser()
config.read('config.ini')

# Constants
GHSearchURI = 'https://api.github.com/search/code'
GH_URI = 'https://api.github.com'
USERNAMES, TOKENS = [config['Account']['userid'], config['Account']['userid_sub']], \
                    [config['Account']['token'], config['Account']['token_sub']]
USERIDX = 0
USERNAME = USERNAMES[USERIDX]
TOKEN = TOKENS[USERIDX]

def switchUser():
    global USERIDX, USERNAME, TOKEN
    USERIDX = 1-USERIDX
    USERNAME = USERNAMES[USERIDX]
    TOKEN = TOKENS[USERIDX]

def reqGet(url: str, params: dict = None):
    """
    request GET Method to github api, avoiding secondary rate limit
    https://docs.github.com/en/rest/overview/resources-in-the-rest-api#secondary-rate-limits
    """
    while 1:
        try:
            checkAPILimit()
            req = requests.get(url, params=params, auth=(USERNAME, TOKEN))
            data = req.json()
            if not 'message' in data.keys() and not 'documentation_url' in data.keys():
                break
            pprint(data)
            # due to secondary limit, you should take a break
            sleep(30)
        except:
            logger('retry...')
            sleep(5)
    return data


def getRateLimit() -> dict:
    # https://docs.github.com/en/rest/reference/rate-limit
    data = {}
    while 1:
        try:
            res = requests.get(GH_URI + '/rate_limit', auth=(USERNAME, TOKEN))
            data = res.json()
            break
        except:
            logger('retry...')
            sleep(3)
            continue
    return data


def getSearchPageByCode(query, pageNo: int = 1) -> dict:
    """
    Get json request from github code search api. see github-api.example.json
    reference:
        https://docs.github.com/en/rest/reference/search
        https://docs.github.com/en/github/searching-for-information-on-github/searching-on-github/searching-code

    The Search API has a custom rate limit.
    For requests using Basic Authentication, OAuth, or client ID and secret,
    you can make up to 30 requests per minute.
    For unauthenticated requests, the rate limit allows you to make up to 10 requests per minute.

    See the rate limit documentation for details on determining your current rate limit status.
    """
    res = reqGet(GH_URI + '/search/code', params={'q': query,
                                                  'per_page': 100,
                                                  'page': pageNo})
    return res


def getCodeFromItem(item: dict) -> str:
    """
    get code from item
    """
    url = item['url']
    data = reqGet(url)
    if data['type'] == 'file':
        return data['content']
    else:
        return ''


def isLimitReached() -> bool:
    data = getRateLimit()["resources"]
    core, search = int(data["core"]["remaining"]), int(data["search"]["remaining"])
    coreReset, searchReset = datetime.fromtimestamp(int(data["core"]["reset"])).time().isoformat(),\
                             datetime.fromtimestamp(int(data["search"]["reset"])).time().isoformat()
    logger(f"{cStr(f'Remaining: core={core} by {coreReset}, search={search} by {searchReset}', 'bk')}")
    return core < 100 or search == 0


def checkAPILimit():
    while isLimitReached():
        logger("API LIMIT is NEAR! Switch user...")
        switchUser()
        logger(f"NOW USER: {cStr(USERNAME, 'br')}")
        sleep(5)
        logger("Work time!")


async def gatherContentsFromUrls(urls: List[str]):
    checkAPILimit()
    async with ClientSession() as session:
        results = await asyncio.gather(*[collectContentFromUrl(session, url) for url in urls])
        return results

async def collectContentFromUrl(session, url: str) -> dict:
    data = None
    while data is None:
       async with session.get(url, auth=BasicAuth(USERNAME, TOKEN)) as resp:
            try:
                data = await resp.json()
                return data
            except Exception as e:
                logger(str(e) + '\t' + url)
                await asyncio.sleep(1)


if __name__ == '__main__':
    from pprint import pprint
    urls = ['https://api.github.com/repositories/328103518/contents/real_time_data_trade.py?ref=7ecb5da6d478290ee0519c38bb6e6a1a997d4e6a',
'https://api.github.com/repositories/341900652/contents/tradeFunctions.py?ref=3996f299e024f5bdb9a1a5085a41c85b50cfb9a3',]
    loop = asyncio.get_event_loop()
    # result = asyncio.run(gatherContentsFromUrls(urls), debug=True)
    result = loop.run_until_complete(gatherContentsFromUrls(urls))
    print(type(result))
    pprint(result)
