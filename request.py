import requests
import base64
import os
import json
from env import Config

# https://docs.github.com/en/rest/reference/search
# https://docs.github.com/en/github/searching-for-information-on-github/searching-on-github/searching-code
'''
The Search API has a custom rate limit. 
For requests using Basic Authentication, OAuth, or client ID and secret, 
you can make up to 30 requests per minute. 
For unauthenticated requests, the rate limit allows you to make up to 10 requests per minute.

See the rate limit documentation for details on determining your current rate limit status.
'''

ghSearchURI = 'https://api.github.com/search/code'
SAVE_PATH = './output/'
username = Config.githubAccount['userid']
token = Config.githubAccount['token']

def getSearchResult(query, pageNo):
    res = requests.get(ghSearchURI,
                       auth =(username, token),
                       params={'q':query,
                               'per_page': 100,
                               'page': pageNo})
    data = res.json()

    saveDir = SAVE_PATH + f"{pageNo}/"
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)
    with open(saveDir + "query.json", 'w', encoding='utf-8') as f:
        f.write(res.text)

    return data

def writeItems(searchResult, pageNo):
    for i, itm in enumerate(searchResult['items']):
        url = itm['url']
        res = requests.get(url,
                       auth =(username, token))
        data = res.json()
        try:
            name, sha, content = data['name'], data['sha'], data['content']
            sourceCode = base64.b64decode(content).decode()

            saveDir = SAVE_PATH + f"{pageNo}/"
            fileName = sha+'.py'

            if not os.path.exists(saveDir):
                os.makedirs(saveDir)
            with open(saveDir + fileName, 'w', encoding='utf-8') as file,\
                    open(saveDir + "index.txt", 'a') as index:
                file.write(sourceCode)
                index.write(f"{fileName} : {name} : {url}")
            print(f"From page {pageNo}, No.{i+1}: {fileName} saved")
        except:
            print("ERROR: ", url)

def main(keyword):
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
    for p in range(1, 11):
        print(f"#### PAGE NO. {p} ####")
        result = getSearchResult(keyword, p)
        writeItems(result, p)

if __name__ == '__main__':
    main("import tensorflow language:python")