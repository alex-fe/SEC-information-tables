import argparse
import csv
import datetime
import os
import sqlite3


SCRIPT_LOC = os.path.join(os.path.dirname(os.path.realpath(__file__)))
SQL_LOC = os.path.join(SCRIPT_LOC, 'sec.sqlite')
CIK_CSV_LOC = os.path.join(SCRIPT_LOC, 'cik.csv')

CIK_TABLE_NAME = 'cik'
STOCKS_TABLE_NAME = 'stocks'

parser = argparse.ArgumentParser()
parser.add_argument('stock', type=str.upper, help='Stock symbol e.g. AAL, AAPL')
parser.add_argument(
    '-s', "--startdate", metavar='Date', nargs='?',
    default=(datetime.datetime.now() + datetime.timedelta(-30)).strft('%Y%m%d'),
    help="Choose a start date in format YYYY-MM-DD. Default is 30 days prior."
)
parser.add_argument(
    '-e', "--enddate", metavar='Date', nargs='?',
    default=datetime.datetime.now().strft('%Y%m%d'),
    help="Choose a start date in format YYYY-MM-DD. Default is today."
)
parser.add_argument(
    '--sql', metavar='Path', nargs='?', default=SQL_LOC,
    help="Path to sqlite database. Default is location is {}".format(SQL_LOC)
)
parser.add_argument(
    '--cik', metavar='Path', nargs='?', default=CIK_CSV_LOC,
    help="Path to cik.csv. Default location is {}".format(CIK_CSV_LOC)
)


def connect(sqlite_file):
    """Make connection to an SQLite database file """
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    return conn, c


def does_table_exist(c, table_name):
    query = "SELECT name FROM sqlite_master"
    query += " WHERE type='table' AND name='{}';".format(table_name)
    c.execute(query)
    return bool(c.fetchone())


def does_data_exist(stock, startdate, enddate, c, columns):
    if not does_table_exist(c, STOCKS_TABLE_NAME):
        query = 'CREATE TABLE {0} (id integer PRIMARY KEY, {1});'
        query = query.format(STOCKS_TABLE_NAME, ','.join(columns))
        c.execute(query)
    c.execute("Select * FROM {} WHERE Ticker=?".format(CIK_TABLE_NAME), (stock,))
    row = c.fetchone()
    query = """SELECT * FROM {} WHERE
            trade_date >= date({})
            AND trade_date <= date({})
            AND cik = {}
            """.format(STOCKS_TABLE_NAME, startdate, enddate)
    t = (startdate, enddate, row['CIK'])
    c.execute(query, t)
    return bool(c.fetchall())


def create_cik_table(c, table_name, cik_path):
    with open(cik_path, 'r') as f:
        reader = csv.reader(f)
        columns = next(reader)[0].replace('|', ',')
        col_len = len(columns.split(','))
        query = 'CREATE TABLE {0} (id integer PRIMARY KEY, {1});'.format(table_name, columns)
        c.execute(query)
        for data in reader:
            query = 'INSERT INTO {0} ({1}) VALUES ({2})'
            query = query.format(table_name, columns, ','.join('?' * col_len))
            print(query, data[0].split('|'))
            c.execute(query, data[0].split('|'))
        return c.lastrowid


def query():
    pass

if __name__ == '__main__':
    user_args = parser.parse_args()
    conn, c = connect(user_args.sql)
    if not does_table_exist(c, CIK_TABLE_NAME):
        create_cik_table(c, CIK_TABLE_NAME, user_args.cik)
    if not does_data_exist():
        pass
    conn.close()

    "https://www.sec.gov/cgi-bin/own-disp?action=getissuer&CIK=0000051143"
