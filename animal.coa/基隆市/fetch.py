# -*- coding: utf-8 -*-
import os
import shutil
import re
import sqlite3
import collections
from urlparse import urlparse, parse_qs
from datetime import date

from bs4 import BeautifulSoup
import requests

html_path = "htmls"
image_url = "http://www.klaphio.gov.tw/uploadfiles/cd/"
base_url = "http://www.klaphio.gov.tw/receiving_notice.php"
github_photo_url = "https://g0v.github.io/animal.coa/%E5%9F%BA%E9%9A%86%E5%B8%82/"
data_schema = collections.OrderedDict((
    (u"進所日期：", "enter_date"),
    (u"進所原因：", "reason"),
    (u"性別：", "gender"),
    (u"毛色：", "color"),
    (u"品種：", "variety"),
    (u"體型：", "body_type"),
    (u"晶片號碼：", "wafer_number"),
    (u"來源地點：", "source")
))

conn = sqlite3.connect('animal.db')


def create_db():
    try:
        c = conn.cursor()
        sql = "CREATE TABLE animals (id, photo, %s);" % ",".join(data_schema.values())
        c.execute(sql)
        print "table animals created."
    except Exception as e:
        print e
        pass


def store_info(data):
    try:
        c = conn.cursor()
        sql = "INSERT INTO animals (id, photo, color, enter_date, source, gender, reason, wafer_number, body_type, variety) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        c.execute(sql, (
            data.get("id"),
            data.get("photo"),
            data.get("color"),
            data.get("enter_date"),
            data.get("source"),
            data.get("gender"),
            data.get("reason"),
            data.get("wafer_number"),
            data.get("body_type"),
            data.get("variety")
        ))
        conn.commit()
    except Exception as e:
        print e
        pass


def ensure_directories(path):
    if not os.path.exists(path):
        os.makedirs(path)


def save_html(path, filename, content):
    with open(os.path.join(path, filename), 'w') as f:
        f.write(content)


def fetch_page(page=1, total=None):
    page = int(page)
    print "Fetching page %d" % page
    r = requests.post(base_url, {"page": page})
    content = r.text.encode('utf-8').strip()
    if r.status_code == 200:
        save_html(html_path, "page-%d.html" % page, content)

    if (page < total):
        fetch_page(page + 1, total=total)
    else:
        return content


def get_total_page(content):
    soup = BeautifulSoup(content)
    total_page_html = soup.find('a', href="javascript:goPage('5');").get('href')
    return int(re.match(r".+goPage\(\'(\d+)\'\)", total_page_html).group(1))


def download_image(filename, animal_id, save_path, save_name):
    if not os.path.exists(os.path.join(save_path, save_name)):
        print "downloading image, id=", animal_id
        ensure_directories(save_path)
        r = requests.get(image_url + filename, stream=True)
        if r.status_code == 200:
            with open(os.path.join(save_path, save_name), 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)


def fetch_detail_page(url):
    detail_url = "%s?%s" % (base_url, url.split('?')[-1])
    qs = parse_qs(urlparse(detail_url).query)
    [animal_id] = qs.get('id')
    animal_id = int(animal_id)

    c = conn.cursor()
    c.execute("SELECT * FROM animals WHERE id=?;", (animal_id,))
    row = c.fetchone()
    if row:
        print "animal id: %d exists, skip fetch" % animal_id
        return

    try:
        with open(os.path.join(html_path, "detail-page-%d.html" % animal_id), 'r') as f:
            print "use detail-page-%d.html cached file." % animal_id
            content = f.read()
    except IOError:
        print "fetching detail page, id =", animal_id
        r = requests.get(detail_url)
        if r.status_code == 200:
            content = r.text.encode('utf-8').strip()
            save_html(html_path, 'detail-page-%d.html' % animal_id, content)

    soup = BeautifulSoup(content)

    data = {
        "id": animal_id
    }

    infos = soup.find("div", class_="word").find_all("li")
    for info in infos:
        title = info.find("span").contents[0]
        title = title.replace(" ", "")
        if title in data_schema.keys():
            animal_info = ""
            try:
                animal_info = info.contents[1]
            except:
                pass

            data[data_schema[title]] = animal_info

    parsed_date = tuple(map(int, data['enter_date'].split('-')))
    y, m, d = parsed_date
    data['enter_date'] = date(y + 1911, m, d).strftime("%Y-%m-%d")

    # download image
    img_src = soup.find("div", class_="photo").select("img")[0].get('src').split('/')[-1]
    filename, ext = os.path.splitext(img_src)
    save_name = filename + ext.lower()
    download_image(img_src, animal_id, data['enter_date'], save_name)
    data["photo"] = github_photo_url + save_name

    print "save data, id=", animal_id
    store_info(data)

if __name__ == "__main__":
    count = 0
    ensure_directories(html_path)
    create_db()
    result = fetch_page()
    total_pages = get_total_page(result)
    print "Total: %d pages" % total_pages
    fetch_page(2, total=total_pages)

    page_files = next(os.walk(html_path))[2]
    for page_file in page_files:
        if not page_file.startswith('page'):
            continue

        with open(os.path.join(html_path, page_file), 'r') as f:
            content = f.read()
            soup = BeautifulSoup(content)
            animals = soup.find("ol", class_="search_img_list").find_all("li")
            for animal in animals:
                href = animal.find('a').get('href')
                fetch_detail_page(href)
                count += 1

    print "Handled %d items." % count
