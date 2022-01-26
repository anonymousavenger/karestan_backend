import re

from pandas import DataFrame


def check_integrity(driver):
    div_list = driver.find_elements_by_css_selector(".message.default.clearfix")
    outs_old = [15, 16, 17, 18, 23, 26, 30, 37, 39, 64, 105, 106, 107, 188, 189, 191, 192, 205, 247, 248, 268, 285, 286,
                290, 291, 292, 296, 297, 326, 332, 341, 349, 354, 367, 371, 373, 374, 389, 398, 401, 405, 406, 407, 410,
                447, 454, 455, 473, 486, 489, 499, 500, 531, 542, 544, 545, 591, 592, 605, 609, 612, 613, 614, 618, 623,
                627, 637, 642, 659, 662, 672, 673, 702, 719, 722, 734, 735, 737, 744, 750, 758, 765, 836, 864, 893, 915,
                916, 942, 945, 984, 1003, 1011, 1018]
    cursor = 10
    outs = []
    for item in div_list:
        cursor += 1
        id_name: str = item.get_attribute("id")
        if id_name.startswith("message-"):
            print(id_name)
            continue
        msg_num = int(id_name.replace("message", ""))
        while cursor < msg_num:
            outs.append(cursor)
            cursor += 1
        if cursor > msg_num:
            raise Exception(f"cursor: {cursor}, msg_num: {msg_num}")
        if msg_num in outs_old:
            print(msg_num)
    return outs, cursor


def run(driver, page):
    errors = []
    df = DataFrame(columns=['raw_text', 'title', 'type', 'slug', 'timestamp'])
    address = f"ChatExport_19_08_2021/messages{page}.html"
    driver.get(address)
    div_list = driver.find_elements_by_css_selector(".message.default.clearfix")
    for el in div_list:
        id_name: str = el.get_attribute("id")
        if id_name.startswith("message-"):
            print(id_name)
            continue
        try:
            df = add_to_df(el, df)
        except Exception as e:
            errors.append(e.args)
    return df, errors


def add_to_df(el, df: DataFrame):
    raw_text = el.find_element_by_class_name("text").text.replace("\n", "")
    timestamp = el.find_element_by_css_selector(".pull_right.date.details").get_attribute("title")
    match = re.findall(r"(.*),?را.*http.*/(.*)/(\d+)", raw_text)
    if len(match) != 1:
        raise Exception(match, raw_text, 'm')
    items = match[0]
    if len(items) != 3:
        raise Exception(el.text, f"bad regex. length:{len(items)}")
    return df.append({
        'raw_text': raw_text,
        'title': items[0],
        'type': items[1],
        'slug': items[2],
        'timestamp': timestamp
    }, ignore_index=True)


if __name__ == "__main__":
    pass
    # Crawler.shutdown()
    # run(driver)
