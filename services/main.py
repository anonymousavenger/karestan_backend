from os.path import isfile
from typing import Literal

from crawler import Crawler
from process_chats import check_integrity, run
import pandas as pd
from random import randint
import atexit
import json
import pickle


@atexit.register
def shutdown():
    Crawler.shutdown()


def crawler_load():
    Crawler.load(
        "file:///ChatExport_19_08_2021/messages1.html")
    return Crawler.get_driver()


def check_existence(file_type: Literal["review", "interview"], start=1, end=1000, channel_start=502):
    missing_files = []
    missing_in_df = []
    existing_files = []
    df = pd.read_pickle("processed_all.p")
    filt = df[df['type'] == file_type]
    for i in range(start, end + 1):
        file_exists = isfile(f"{file_type}s/{i}.html")
        if not file_exists:
            if not filt[filt['slug'] == str(i)].empty or i < channel_start:
                missing_files.append(i)
        else:
            existing_files.append(i)
            if i >= channel_start and filt[filt['slug'] == str(i)].empty:
                missing_in_df.append(i)
    return {
        'type': file_type,
        'missing_files': missing_files,
        'missing_in_df': missing_in_df,
        'existing_files': existing_files,
        'total': len(filt) + len(missing_in_df) + channel_start - 1
    }


def test():
    res = []
    for j in range(0, 1000000):
        res.append(randint(0, 10000))
    with open("temp1.json", "w+") as h:
        json.dump(res, h)


if __name__ == '__main__':
    # test()
    reviews = check_existence("review", 1, 2804, 522)
    interviews = check_existence("interview", 1, 1184, 133)
    # df = pd.read_pickle("processed_all.p")
    # df1:pd.DataFrame = df[df['type'] == 'review']
    # df2 = df1.sort_values(by='slug',axis=0)
