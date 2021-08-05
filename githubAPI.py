import requests
from env import Config

githubURI = 'https://api.github.com/'
username = Config.githubAccount['userid']
token = Config.githubAccount['token']

def getRateLimit():
    # https://docs.github.com/en/rest/reference/rate-limit
    res = requests.get(githubURI+'/rate_limit', auth = (username, token))
    return res.json()