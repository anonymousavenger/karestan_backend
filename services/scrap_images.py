import os
import shutil
import json
from typing import Optional

import requests

DEFUALT_LOGO = ""


def get_image(url, file_name):
    # url = "https://media.jobguy.work/company/22/d06e6600-4091-11e9-803e-b5a47c44fbbb.jpg"
    res = requests.get(url, stream=True)
    if res.status_code == 200:
        with open(file_name, "wb") as h:
            res.raw.decode_content = True
            shutil.copyfileobj(res.raw, h)
    else:
        raise Exception('request_failed')


def get_all_subdirs(path: str = "companies"):
    return os.listdir(path)


def get_image_links(path="companies/cafebazaar"):
    try:
        with open(path + "/info.json", "r") as h:
            info = json.load(h)
    except:
        raise Exception('no_file')
    success: dict = info.get("success")
    data: dict = info.get("data")

    if data is None or success is None:
        raise Exception('bad_main_keys')
    if not info["success"]:
        raise Exception('unsuccessful_request')
    logo = exists_or_none(data.get("logo"))
    cover = exists_or_none(data.get("cover"))
    gallery = data.get("gallery")
    new_gallery = {}
    if gallery is not None:
        for key, item in enumerate(gallery):
            new_gallery[f"gallery_{key}"] = item.get('path')
    return {
        "logo": logo,
        "cover": cover,
        **new_gallery
    }


def exists_or_none(url: Optional[str]):
    if url is None or url.find("/default/") != -1:
        return None
    else:
        return url


def run(start=0):
    base_url = "https://media.jobguy.work"
    sub_dirs = get_all_subdirs("companies")[start:-1]
    errors = {}
    subdirs_number = len(sub_dirs)
    for key, sub_dir in enumerate(sub_dirs):
        print(f"Getting {sub_dir} ({key + 1} of {subdirs_number})")
        try:
            links = get_image_links(f"companies/{sub_dir}")
        except Exception as e:
            message = e.args[0]
            print(f"Error: {message}")
            errors["sub_dir"] = message
            continue
        error = {}
        for name, url in links.items():
            if url is None:
                continue
            try:
                get_image(url=base_url + url, file_name=f"companies/{sub_dir}/{name}.jpg")
            except Exception as e:
                message = e.args[0]
                print(f"Error: {message}")
                error[name] = message
        if len(error) > 0:
            errors[sub_dir] = error
    with open("output.json", "w+") as h:
        json.dump(errors, h)
    return errors
