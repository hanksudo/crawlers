# animal.coa

各縣市公立動物收容所資訊統整系統 

- https://g0v.hackpad.com/JBhVDOPxhxe
- https://github.com/g0v/animal.coa

## 基隆市

```bash
pip install -r requirements.txt

# normal version with Requests
python crawler.py

# concurrent version with Twisted
python crawler-concurrent.py
```

## 金門縣

```bash
# gevent and future.concurrent
python crawler.py

ll files/*.xls | wc -l

# xls to csv (LiberOffice required)
pip install unoconv
unoconv -f csv files/*.xls

ll files/*.csv | wc -l
python extract.py
```
