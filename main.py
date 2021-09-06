import sqlite3
from githubAPI import *
from configparser import ConfigParser
from datetime import datetime
from time import sleep

config = ConfigParser()
config.read('config.ini')
DATABASE = config['General']['database']
PAGE_IDX = int(config['Checkpoint']['crawled_page'])+1
TARGET_PAGES = int(config['General']['target_pages'])
QUERY = config['General']['query']

"""
TABLE data
id : INTEGER
name: TEXT
sha : TEXT
url : TEXT
code : TEXT(BASE 64)
extension : TEXT
"""
def logger(text:str):
    t = datetime.fromtimestamp(int(datetime.now().timestamp())).isoformat()
    print(t,'\t', text)

def checkDB():
    conn = sqlite3.connect(DATABASE)
    curr = conn.cursor()
    curr.execute("SELECT name FROM sqlite_master WHERE type='table'")
    lst = curr.fetchall()
    if len(lst) < 1:
        curr.execute("CREATE TABLE data(id integer primary key autoincrement, name TEXT, sha TEXT unique , url TEXT, code TEXT, extension TEXT)")
    conn.close()

def pushItemToDB(item):
    name = item['name']
    sha = item['sha']
    url = item['url']
    ext = name.split('.')[-1]
    code = getCodeFromItem(item)

    conn = sqlite3.connect(DATABASE)
    curr = conn.cursor()
    curr.executemany('INSERT OR IGNORE INTO data (name, sha, url, code, extension) VALUES (?, ?, ?, ?, ?)',
                     [(name, sha, url, code, ext)])
    conn.commit()
    conn.close()

def pushRowsToDB(names:list, shas:list, urls:list, codes:list, extensions: list) -> None:
    conn = sqlite3.connect(DATABASE)
    curr = conn.cursor()
    curr.executemany('INSERT OR IGNORE INTO data (name, sha, url, code, extension) VALUES (?, ?, ?, ?, ?)',
                     zip(names,shas,urls,codes,extensions))
    conn.commit()
    conn.close()
def isDuplicated(value: str) -> bool:
    conn = sqlite3.connect(DATABASE)
    curr = conn.cursor()
    val = curr.execute("SELECT 1 FROM data WHERE sha=?", (value,)).fetchall()
    conn.close()
    return  bool(val)

def isLimitReached() -> bool:
    data = getRateLimit()["resources"]
    core, search = int(data["core"]["remaining"]), int(data["search"]["remaining"])
    logger(f"Remaining limits: core={core}, search={search}")
    return core == 0 or search == 0

def checkAPILimit():
    if isLimitReached():
        logger("API LIMIT REACHED! Nap time...")
        sleep(600)
        logger("Work time!")

def saveCheckpoint(crawledPage: int) -> None:
    config['Checkpoint']['crawled_page'] = str(crawledPage)
    with open('config.ini', 'w') as f:
        config.write(f)

def crawlPage(pageNo:int) -> bool:
    try:
        page = getSearchPageByCode(QUERY, pageNo)
        names, shas, urls, codes, extensions = [], [], [], [], []
        logger(f"CRAWLING Page #{pageNo}")
        for item in page['items']:
            checkAPILimit()
            if isDuplicated(item['sha']):
                logger(f"Page #{pageNo}, {item['name']} is DUPLICATED")
                continue
            names.append(item['name'])
            shas.append(item['sha'])
            codes.append(getCodeFromItem(item))
            extensions.append(item['name'].split('.')[-1])
            logger(f"Page #{pageNo}, {item['name']} has CRAWLED")
            pushItemToDB(item)
        logger(f"Page #{pageNo} DONE")
        # pushRowsToDB(names, shas, urls, codes, extensions)
        # logger(f"Saved to DB.")
        return True

    except Exception as e:
        logger(f"Failed to crawl Page #{pageNo}, due to {e}")
        return False

def doCrawl():
    logger("Initiate database...")
    checkDB()
    logger(f"start crawling:\nquery:{QUERY}, target_pages:{TARGET_PAGES}, crawled_page:{PAGE_IDX-1}")
    for p in range(PAGE_IDX, TARGET_PAGES+1):
        checkAPILimit()
        crawlPage(p)
        saveCheckpoint(p)


if __name__ == '__main__':
    doCrawl()

