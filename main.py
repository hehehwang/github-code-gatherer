"""
github scrapper by code
due to 1,000 result limits by github api,
this program crawls 1,000 codes for each byte.

flow: doCrawlBySize -> searchQuery -> crawlPage -> pushItemsToDB
+------------+----------------------------------------------------------+
| Table name |                           data                           |
+------------+---------+----------------------------+-------------------+
| column     | type    | property                   | description       |
+------------+---------+----------------------------+-------------------+
| id         | INTEGER | Primary key, Autoincrement |                   |
+------------+---------+----------------------------+-------------------+
| file_name  | TEXT    |                            | name of file      |
+------------+---------+----------------------------+-------------------+
| path_name  | TEXT    |                            | path of file      |
+------------+---------+----------------------------+-------------------+
| sha        | TEXT    | Unique                     |                   |
+------------+---------+----------------------------+-------------------+
| url        | TEXT    |                            |                   |
+------------+---------+----------------------------+-------------------+
| code       | TEXT    |                            | encoded by base64 |
+------------+---------+----------------------------+-------------------+
| extension  | TEXT    |                            | extension         |
+------------+---------+----------------------------+-------------------+
| Q          | TEXT    |                            | query             |
+------------+---------+----------------------------+-------------------+
"""
import sqlite3
from pprint import pformat

from githubAPI import *
import asyncio

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


def errLogger(data: dict, error: Exception):
    t = datetime.fromtimestamp(int(datetime.now().timestamp())).isoformat()
    with open('err.log', 'a', encoding='utf-8') as f:
        f.write(str(t) + '\t' + str(error) + '\n')
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
    return bool(val)


def saveCheckpoint() -> None:
    config['Checkpoint']['crawled_size'] = str(CRAWLED_SIZE)
    config['Checkpoint']['crawled_page'] = str(CRAWLED_PAGE)
    with open('config.ini', 'w') as f:
        config.write(f)


def pushItemsToDB(items: list):
    conn = sqlite3.connect(DATABASE)
    curr = conn.cursor()
    for item in items:
        file_name = item['file_name']
        file_path = item['file_path']
        sha = item['sha']
        url = item['url']
        query = item['query']
        ext = file_name.split('.')[-1]
        code = item['code']
        curr.execute(
            'INSERT OR IGNORE INTO data (file_name, file_path, sha, url, code, extension, Q) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (file_name, file_path, sha, url, code, ext, query))
    conn.commit()
    conn.close()


def crawlPage(sizedQuery: str, pageNo: int) -> bool:
    page = getSearchPageByCode(sizedQuery, pageNo)
    logger(f"CRAWLING Page #{pageNo}")
    items = []
    urls = []
    shaList = []
    for item in page['items']:
        if isDuplicated(item['sha']) or item['sha'] in shaList:
            logger(f"#{CRAWLED_SIZE + 1}-{pageNo}, {cStr(item['name'], 'g')} is {cStr('DUPLICATED', 'r')}")
            continue
        shaList.append(item['sha'])
        bag = {'file_name':item['name'], 'file_path':item['path'], 'sha': item['sha'],
               'url': item['url'], 'query': sizedQuery}
        urls.append(item['url'])
        items.append(bag)


    loop = asyncio.get_event_loop()
    contents = loop.run_until_complete(gatherContentsFromUrls(urls))
    for i in range(len(urls)):
        item = items[i]
        content = contents[i]
        try:
            if content['type'] != 'file':
                logger(f"#{CRAWLED_SIZE + 1}-{pageNo}, {cStr(item['file_name'], 'g')} is {cStr('NOT A FILE', 'bg')}")
                continue
            items[i]['code'] = content['content']
            logger(f"#{CRAWLED_SIZE + 1}-{pageNo}, {cStr(item['file_name'], 'g')} is {cStr('CRAWLED', 'bb')}")
        except Exception as e:
            logger(f"#{CRAWLED_SIZE + 1}-{pageNo}, {cStr(item['file_name'], 'g')} is {cStr('ERROR', 'br')} due to {str(e)}")
            continue

    logger(f"== Page #{pageNo} DONE ==")
    pushItemsToDB(items)
    logger(f"{cStr('Saved to DB.', 'b')}")
    return True


def searchQuery(sizeIdx):
    global CRAWLED_PAGE
    sizedQuery = QUERY + f" size:{sizeIdx}..{sizeIdx + 1}"
    page = getSearchPageByCode(sizedQuery)
    # try
    results = min(1000, page['total_count'])
    if not results:
        logger(f"NO RESULTS IN {sizeIdx} to {sizeIdx + 1}!!")
    else:
        logger(
            f"Found {cStr(page['total_count'], 'br')} codes, Crawling page: {CRAWLED_PAGE + 1} to {results // 100}")
        while CRAWLED_PAGE < results // 100:
            pageToCrawl = CRAWLED_PAGE + 1
            crawlPage(sizedQuery, pageToCrawl)
            CRAWLED_PAGE += 1
            saveCheckpoint()
            sleep(5)

        return True

    # except Exception as e:
    #     logger(f"!!!! {cStr('Failed', 'r')} to crawl Size #{sizeIdx}, due to {e} !!!!")
    #     errLogger(page, e)
    #     return False


def doCrawlBySize():
    global CRAWLED_SIZE, CRAWLED_PAGE

    logger("Initiate database...")
    checkDB()
    logger(f"""start crawling:\nQUERY:{cStr(QUERY, 'bm')}, target_size:{CRAWLED_SIZE}, crawled_page:{CRAWLED_PAGE}""")
    while CRAWLED_SIZE < 300_000:
        sizeToCrawl = CRAWLED_SIZE + 1
        logger(f"Crawling size: {cStr(sizeToCrawl, 'br')}byte")
        if searchQuery(sizeToCrawl):
            logger(f"=== size loop done ===")
            CRAWLED_PAGE = 0
            CRAWLED_SIZE += 1
            saveCheckpoint()
        else:
            logger("error occurred, but we're keep going anyway")


if __name__ == '__main__':
    # {'incomplete_results': False, 'items': [], 'total_count': 0}
    # pprint(getSearchPageByCode("extension:py size:10..11 NOT filename:__init__.py import tensorflow", 1))
    # print(type(sqlite3.connect(':memory:')))
    doCrawlBySize()
