# -*- coding: utf-8 -*-
import sqlite3
import csv

conn = sqlite3.connect('animal.db')
conn.row_factory = sqlite3.Row

c = conn.cursor()
c.execute("SELECT DISTINCT(enter_date) FROM animals;")
for (day,) in c.fetchall():
    with open('%s.csv' % day, 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(["來源地點", "入園日期", "品種", "備註", "性別", "收容原因", "晶片號碼", "毛色", "體型", "相片網址"])
        c.execute("SELECT * FROM animals WHERE enter_date = ? ORDER BY id;", (day,))
        for row in c.fetchall():
            data = [
                row["source"].encode('utf-8'),
                row["enter_date"].encode('utf-8'),
                row["variety"].encode('utf-8'),
                u"",
                row["gender"].encode('utf-8'),
                row["reason"].encode('utf-8'),
                row["wafer_number"].encode('utf-8'),
                row["color"].encode('utf-8'),
                row["body_type"].encode('utf-8'),
                row["photo"].encode('utf-8')
            ]
            spamwriter.writerow(data)
