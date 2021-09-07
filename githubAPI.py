from pprint import pprint
from configparser import ConfigParser
import requests
import base64

config = ConfigParser()
config.read('config.ini')

# Constants
GHSearchURI = 'https://api.github.com/search/code'
GH_URI = 'https://api.github.com'
USERNAME = config['Account']['userid']
TOKEN = config['Account']['token']

def reqGet(url:str, params: dict = None):
    return requests.get(url, params=params, auth = (USERNAME, TOKEN)).json()

def getRateLimit() -> dict:
    # https://docs.github.com/en/rest/reference/rate-limit
    res = requests.get(GH_URI+'/rate_limit', auth = (USERNAME, TOKEN))
    return res.json()

def getSearchPageByCode(query, pageNo:int) -> dict:
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
    :param query:
    :param pageNo:
    :return:
    """
    # res = requests.get(GH_URI+'/search/code',
    #                    auth=(USERNAME, TOKEN),
    #                    params={'q': QUERY,
    #                            'per_page': 100,
    #                            'page': pageNo})
    res = reqGet(GH_URI+'/search/code', params = {'q': query,
                                                  'per_page': 100,
                                                  'page': pageNo})
    return res

def getCodeFromItem(item: dict) -> str:
    """
    get code from item
    :param item:
    :return:
    """
    url = item['url']
    data = reqGet(url)
    return data['content']

if __name__ == '__main__':
    pass