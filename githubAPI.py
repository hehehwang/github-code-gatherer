from configparser import ConfigParser

from time import sleep
from common import *

import requests

config = ConfigParser()
config.read('config.ini')

# Constants
GHSearchURI = 'https://api.github.com/search/code'
GH_URI = 'https://api.github.com'
USERNAME = config['Account']['userid']
TOKEN = config['Account']['token']


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
            sleep(3)
        except:
            logger('retry...')
            sleep(3)
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
    logger(f"{cStr(f'Remaining limits: core={core}, search={search}', 'bk')}")
    return core == 0 or search == 0


def checkAPILimit():
    if isLimitReached():
        logger("API LIMIT REACHED! Nap time...")
        sleep(300)
        logger("Work time!")


if __name__ == '__main__':
    pass
