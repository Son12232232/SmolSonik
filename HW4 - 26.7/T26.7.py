# schedule_regex.py
import requests
import re

def fetch_html(station_code):
    url = f"https://gd.tickets.ua/uk/railwaytracker/table/~{station_code}"
    resp = requests.get(url)
    resp.encoding = 'windows-1251'
    return resp.text

def extract_tables(html):
    return re.findall(r'<table[^>]*>(.*?)</table>', html, flags=re.S)

def parse_table_rows(tbl_html):
    rows = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', tbl_html, flags=re.S):
        cols = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, flags=re.S)
        # очищаємо від решти тегів
        cols = [re.sub(r'<.*?>', '', cell).strip() for cell in cols]
        if cols:
            rows.append(cols)
    return rows

def main():
    station = input("Код станції: ")
    html = fetch_html(station)
    tables = extract_tables(html)

    arrivals, departures = [], []
    for tbl in tables:
        if re.search(r'Прибутт', tbl):
            arrivals = parse_table_rows(tbl)
        elif re.search(r'Відправл', tbl):
            departures = parse_table_rows(tbl)

    print("\n=== Прибуття ===")
    for row in arrivals:
        print('\t'.join(row))

    print("\n=== Відправлення ===")
    for row in departures:
        print('\t'.join(row))

if __name__ == "__main__":
    main()
