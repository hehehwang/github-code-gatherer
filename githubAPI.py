import requests
from env import Config

__githubURI = 'https://api.github.com'
__username = Config.githubAccount['userid']
__token = Config.githubAccount['token']

def getRateLimit():
    # https://docs.github.com/en/rest/reference/rate-limit
    res = requests.get(__githubURI+'/rate_limit', auth = (__username, __token))
    return res.json()