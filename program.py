import argparse
import csv
import os
import sqlite3
from datetime import datetime, timedelta
from urllib.request import urlopen

from bs4 import BeautifulSoup


SCRIPT_LOC = os.path.join(os.path.dirname(os.path.realpath(__file__)))
SQL_LOC = os.path.join(SCRIPT_LOC, 'sec.db')
CIK_CSV_LOC = os.path.join(SCRIPT_LOC, 'cik.csv')

CIK_TABLE_NAME = 'cik'
STOCKS_TABLE_NAME = 'stocks'
STOCKS_TABLE_COLUMNS = [
    'cik', 'transaction_date', 'reporting_owner', 'position', 'transaction_type',
    'securities_transacted', 'securities_owned', 'owner_cik',
]

parser = argparse.ArgumentParser()
parser.add_argument('stock', type=str.upper, help='Stock symbol e.g. AAL, AAPL')
parser.add_argument('-c', '--cik', help="Company's CIK identifier")
parser.add_argument(
    '-s', "--startdate", metavar='Date', nargs='?',
    default=(datetime.now() + timedelta(-30)).strftime('%Y%m%d'),
    help="Choose a start date in format YYYY-MM-DD. Default is 30 days prior."
)
parser.add_argument(
    '-e', "--enddate", metavar='Date', nargs='?',
    default=datetime.now().strftime('%Y%m%d'),
    help="Choose a start date in format YYYY-MM-DD. Default is today."
)
parser.add_argument(
    '--sql', metavar='Path', nargs='?', default=SQL_LOC,
    help="Path to sqlite database. Default is location is {}".format(SQL_LOC)
)
parser.add_argument(
    '--cikpath', metavar='Path', nargs='?', default=CIK_CSV_LOC,
    help="Path to cik.csv. Default location is {}".format(CIK_CSV_LOC)
)


def create_cik_table(c, conn, cik_path):
    with open(cik_path, 'r') as f:
        reader = csv.reader(f)
        columns = next(reader)[0].replace('|', ',')
        col_len = len(columns.split(','))
        query = 'CREATE TABLE IF NOT EXISTS {} ({});'
        query = query.format(CIK_TABLE_NAME, columns)
        c.execute(query)
        for data in reader:
            query = 'INSERT INTO {} ({}) VALUES ({});'
            query = query.format(CIK_TABLE_NAME, columns, ','.join('?' * col_len))
            c.execute(query, data[0].split('|'))
            conn.commit()


def create_stock_table(cik, startdate, enddate, c, conn):
    query = 'CREATE TABLE IF NOT EXISTS {} ({});'
    query = query.format(STOCKS_TABLE_NAME, ','.join(STOCKS_TABLE_COLUMNS))
    c.execute(query)
    query = (
        'SELECT * FROM {} WHERE transaction_date >= date({})'
        ' AND transaction_date <= date({}) AND cik = {}'
        .format(STOCKS_TABLE_NAME, startdate, enddate, cik)
    )
    c.execute(query)
    if not bool(c.fetchall()):
        owners = query_owners(cik)
        trades = query_transactions(cik, owners, startdate)
        query = 'INSERT INTO {} ({}) VALUES ({})'
        columns = ','.join(STOCKS_TABLE_COLUMNS)
        col_len = len(STOCKS_TABLE_COLUMNS)
        query = query.format(STOCKS_TABLE_NAME, columns, ','.join('?' * col_len))
        c.executemany(query, trades)
        conn.commit()


def query(cik, page_num=0):
    url = 'https://www.sec.gov/cgi-bin/own-disp?action=getissuer&CIK={}'
    url = url.format(cik)
    if page_num:
        url += '&type=&dateb=&owner=include&start=0'.format(page_num)
    print('Page number: {}\n{}'.format(page_num, url))
    try:
        page = urlopen(url)
    except Exception as e:
        return None
    else:
        return page


def query_owners(cik):
    page = query(cik)
    soup = BeautifulSoup(page, 'html.parser')
    owners_table = soup.find(
        'table', {'border': 1, 'cellspacing': 0, 'cellpadding': 3}
    )
    rows = owners_table.find_all('tr')
    owners = {}
    for body, row in enumerate(rows):
        if not body:
            continue
        cells = row.find_all('td')
        owner = cells[0].find(text=True)
        position = cells[3].find(text=True)
        owners[owner] = position
    return owners


def query_transactions(cik, owners, startdate, desired_trans_type='P-Purchase'):
    page_num = 0
    trades = []
    last_transaction = datetime.now()
    startdate = datetime.strptime(startdate, '%Y%m%d')
    while True:
        page = query(cik, page_num)
        if page is None:
            return trades
        else:
            page_num += 80
            soup = BeautifulSoup(page, 'html.parser')
            transactions = soup.find('table', {'id': 'transaction-report'})
            rows = transactions.find_all('tr')
            for body, row in enumerate(rows):
                if not body:
                    continue
                cells = row.find_all('td')
                transaction_date = cells[1].find(text=True)
                owner = cells[3].find(text=True)
                transaction_type = cells[5].find(text=True)
                num_transaction = cells[7].find(text=True)
                num_owned = cells[8].find(text=True)
                owner_cik = cells[10].find(text=True)
                if transaction_type == desired_trans_type:
                    trades.append((
                        cik, transaction_date, owner, owners.get(owner, None),
                        transaction_type, num_transaction, num_owned, owner_cik
                    ))
                last_transaction = datetime.strptime(transaction_date, '%Y-%m-%d')
            if last_transaction <= startdate:
                return trades


if __name__ == '__main__':
    user_args = parser.parse_args()
    conn = sqlite3.connect(user_args.sql)
    c = conn.cursor()
    if user_args.cik:
        cik = user_args.cik
    else:
        try:
            c.execute(
                "Select * FROM {} WHERE Ticker=?".format(CIK_TABLE_NAME),
                (user_args.stock,)
            )
        except sqlite3.OperationalError:
            create_cik_table(c, conn, user_args.cikpath)
            c.execute(
                "Select * FROM {} WHERE Ticker=?".format(CIK_TABLE_NAME),
                (user_args.stock,)
            )
        finally:
            row = c.fetchone()
            cik = row[0]
    create_stock_table(cik, user_args.startdate, user_args.enddate, c, conn)
    conn.close()
