from datetime import datetime
from typing import Union


def logger(text: str):
    t = datetime.fromtimestamp(int(datetime.now().timestamp())).isoformat()
    print(t, '\t', text)


def cStr(text: Union[str, int], colorCode: str) -> str:
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
