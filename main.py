import sqlite3
from githubAPI import *
from configparser import ConfigParser
from datetime import datetime
from pprint import pprint, pformat
from typing import Union

config = ConfigParser()
config.read('config.ini')
DATABASE = config['General']['database']
CRAWLED_PAGE = int(config['Checkpoint']['crawled_page'])
CRAWLED_SIZE = int(config['Checkpoint']['crawled_size'])
QUERY = config['General']['query']
"""
TABLE data
id : INTEGER
file_name: TEXT
file_path: TEXT
sha : TEXT
url : TEXT
code : TEXT(BASE 64)
extension : TEXT
Q : TEXT
"""

def logger(text:str):
    t = datetime.fromtimestamp(int(datetime.now().timestamp())).isoformat()
    print(t,'\t', text)

def cStr(text:Union[str, int], colorCode:str) -> str:
    """
    https://sosomemo.tistory.com/59
    """
    c2c = {
        "k": 30,
        "r": 31,
        "g": 32,
        "y": 33,
        "b": 34,
        "m": 35,
        "c": 36,
        "w": 37,
        "bk": 90,
        "br": 91,
        "bg": 92,
        "by": 93,
        "bb": 94,
        "bm": 95,
        "bc": 96,
        "bw": 97
    }
    return f"\033[{c2c[colorCode]}m{str(text)}\033[0m"

def errLogger(data:dict, error:Exception):
    t = datetime.fromtimestamp(int(datetime.now().timestamp())).isoformat()
    with open('err.log', 'a') as f:
        f.write(str(t)+ '\t' + str(error) + '\n')
        f.write(pformat(data))

def checkDB():
    conn = sqlite3.connect(DATABASE)
    curr = conn.cursor()
    curr.execute("SELECT name FROM sqlite_master WHERE type='table'")
    lst = curr.fetchall()
    if len(lst) < 1:
        curr.execute("CREATE TABLE data(id integer primary key autoincrement, \
        file_name TEXT, file_path TEXT, sha TEXT unique , url TEXT, code TEXT, extension TEXT, Q TEXT)")
    conn.close()

def isDuplicated(value: str) -> bool:
    conn = sqlite3.connect(DATABASE)
    curr = conn.cursor()
    val = curr.execute("SELECT 1 FROM data WHERE sha=?", (value,)).fetchall()
    conn.close()
    return  bool(val)

def saveCheckpoint() -> None:
    config['Checkpoint']['crawled_size'] = str(CRAWLED_SIZE)
    config['Checkpoint']['crawled_page'] = str(CRAWLED_PAGE)
    with open('config.ini', 'w') as f:
        config.write(f)

def pushItemsToDB(items:list):
    conn = sqlite3.connect(DATABASE)
    curr = conn.cursor()
    for item in items:
        file_name = item['name']
        file_path = item['path']
        sha = item['sha']
        url = item['url']
        query = item['query']
        ext = file_name.split('.')[-1]
        code = item['code']
        curr.execute('INSERT OR IGNORE INTO data (file_name, file_path, sha, url, code, extension, Q) VALUES (?, ?, ?, ?, ?, ?, ?)',
                         (file_name, file_path, sha, url, code, ext, query))
    conn.commit()
    conn.close()


def crawlPage(sizedQuery:str, pageNo:int) -> bool:
    page = getSearchPageByCode(sizedQuery, pageNo)
    logger(f"CRAWLING Page #{pageNo}")
    items = []

    try:
        for item in page['items']:
            if isDuplicated(item['sha']):
                logger(f"#{CRAWLED_SIZE+1}-{pageNo}, {cStr(item['name'], 'g')} is {cStr('DUPLICATED', 'r')}")
                continue

            try:
                item['code'] = getCodeFromItem(item)
            except Exception as e:
                logger(f"{CRAWLED_SIZE+1}-{pageNo}, {cStr(item['name'], 'g')} has {cStr('FAILED', 'br')} due to {str(e)}")
                continue

            if not item['code']:
                logger(f"#{CRAWLED_SIZE+1}-{pageNo}, {cStr(item['name'], 'g')} is {cStr('NOT A FILE', 'bg')}")
                continue

            item['query'] = sizedQuery
            items.append(item)
            logger(f"#{CRAWLED_SIZE+1}-{pageNo}, {cStr(item['name'], 'g')} is {cStr('CRAWLED', 'bb')}")
        logger(f"== Page #{pageNo} DONE ==")
        pushItemsToDB(items)
        logger(f"{cStr('Saved to DB.', 'b')}")
        return True

    except Exception as e:
        logger(f"!!!! {cStr('Failed', 'r')} to crawl Page #{pageNo}, due to {e} !!!!")
        errLogger(page, e)
        return False

def searchQuery(sizeIdx):
    global CRAWLED_PAGE
    sizedQuery = QUERY+f" size:{sizeIdx}..{sizeIdx+1}"
    page = getSearchPageByCode(sizedQuery)
    try:
        results = min(1000, page['total_count'])
        if not results:
            logger(f"NO RESULTS IN {sizeIdx} to {sizeIdx+1}!!")
        else:
            logger(f"Found {cStr(page['total_count'], 'br')} codes, Crawling page: {CRAWLED_PAGE+1} to {results//100+1}")
            while CRAWLED_PAGE < results//100+1:
                pageToCrawl = CRAWLED_PAGE + 1
                if crawlPage(sizedQuery, pageToCrawl):
                    CRAWLED_PAGE += 1
                    saveCheckpoint()
                else:
                    logger("error occurred, but we keep going anyway")
                    return False

        return True

    except Exception as e:
        logger(f"!!!! {cStr('Failed', 'r')} to crawl Size #{sizeIdx}, due to {e} !!!!")
        errLogger(page, e)
        return False

def doCrawlBySize():
    global CRAWLED_SIZE, CRAWLED_PAGE

    logger("Initiate database...")
    checkDB()
    logger(f"""start crawling:\nQUERY:{cStr(QUERY, 'bm')}, target_size:{CRAWLED_SIZE}, crawled_page:{CRAWLED_PAGE}""")
    while CRAWLED_SIZE < 300_000:
        sizeToCrawl = CRAWLED_SIZE+1
        logger(f"Crawling size: {cStr(sizeToCrawl, 'br')}byte")
        if searchQuery(sizeToCrawl):
            logger(f"=== size loop done ===")
            CRAWLED_PAGE = 0
            CRAWLED_SIZE += 1
            saveCheckpoint()
        else:
            logger("error occurred, but we keep going anyway")




if __name__ == '__main__':
    # {'incomplete_results': False, 'items': [], 'total_count': 0}
    # pprint(getSearchPageByCode("extension:py size:10..11 NOT filename:__init__.py import tensorflow", 1))
    # print(type(sqlite3.connect(':memory:')))
    doCrawlBySize()
