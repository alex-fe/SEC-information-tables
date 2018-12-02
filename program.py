import argparse
import datetime
import os
import sys
from urllib.request import urlopen

import pandas as pd
from bs4 import BeautifulSoup


SCRIPT_LOC = os.path.join(os.path.dirname(os.path.realpath(__file__)))
CIK_CSV_LOC = os.path.join(SCRIPT_LOC, 'cik.csv')
PICKLE_LOC_1 = os.path.join(SCRIPT_LOC, 'cik_dataframe.pickle')
PICKLE_LOC_2 = os.path.join(SCRIPT_LOC, 'sec_dataframe.pickle')
HTML_LOC = os.path.join(SCRIPT_LOC, 'tables.html')

CIK_TABLE_NAME = 'cik'
STOCKS_TABLE_NAME = 'stocks'
SHOW_COLUMNS = [
    'CIK', 'Transaction Date', 'Reporting Owner', 'Position', 'Transaction Type',
    'Number of Securities Owned', 'Number of Securities Transacted', 'Line Number',
    'Owner CIK',
]


def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


parser = argparse.ArgumentParser()
parser.add_argument('stock', type=str.upper, help='Stock symbol e.g. AAL, AAPL')
parser.add_argument('-c', '--cik', type=str.strip, help="Company's CIK identifier")
parser.add_argument('--html', action='store_true', help='Return sql to html table.')
parser.add_argument('-p', '--position', help="Restrict search by position e.g. CEO")
parser.add_argument(
    '-s', "--startdate", metavar='Date', nargs='?', type=valid_date,
    default=datetime.datetime.now() + datetime.timedelta(-30),
    help="Choose a start date in format YYYY-MM-DD. Default is 30 days prior."
)
parser.add_argument(
    '-e', "--enddate", metavar='Date', nargs='?', type=valid_date,
    default=datetime.datetime.now(),
    help="Choose a start date in format YYYY-MM-DD. Default is today."
)
parser.add_argument(
    '--cikpath', metavar='Path', nargs='?', default=CIK_CSV_LOC,
    help="Path to cik.csv. Default location is {}".format(CIK_CSV_LOC)
)


def create_stock_table(cik, startdate, enddate):
    sec_df = None
    if os.path.isfile(PICKLE_LOC_2):
        sec_df = pd.read_pickle(PICKLE_LOC_2)
        slice = sec_df.loc[
            sec_df['cik'] == cik
            & sec_df['Transaction Date'] >= startdate
            & sec_df['Transaction Date'] <= enddate
        ]
    else:
        slice = pd.Series()
    if slice.empty:
        owners = query_owners(cik)
        trades = query_transactions(cik, startdate)
        trade_df = pd.concat(trades, sort=False, ignore_index=True)
        trade_df['Position'] = trade_df.apply(
            lambda row: owners.get(row['Reporting Owner'], None), axis=1
        )
        trade_df['CIK'] = cik
        if sec_df is not None:
            sec_df = sec_df.append(trade_df)
        else:
            sec_df = trade_df
        sec_df.to_pickle(PICKLE_LOC_2)
        return sec_df.loc[
            sec_df['cik'] == cik
            & sec_df['Transaction Date'] >= startdate
            & sec_df['Transaction Date'] <= enddate
        ]
    else:
        return slice


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


def query_transactions(cik, startdate, transaction_type='P-Purchase'):
    page_num = 0
    trades = []
    last_transaction = datetime.datetime.now()
    while True:
        page = query(cik, page_num)
        if page is None:
            return trades
        else:
            page_num += 80
            soup = BeautifulSoup(page, 'html.parser')
            trade_df = pd.read_html(
                soup.prettify(), attrs={'id': 'transaction-report'}, header=0
            )[0]
            trade_df['Transaction Date'] = pd.to_datetime(
                trade_df['Transaction Date']
            )
            last_transaction = min(trade_df['Transaction Date'])
            tdf = trade_df[trade_df['Transaction Type'] == transaction_type]
            trades.append(tdf)
            if last_transaction <= startdate:
                return trades


if __name__ == '__main__':
    user_args = parser.parse_args()
    if user_args.cik:
        cik = user_args.cik
    else:
        if os.path.isfile(PICKLE_LOC_1):
            cik_df = pd.read_pickle(PICKLE_LOC_1)
        else:
            cik_df = pd.read_csv(user_args.cikpath, sep='|', dtype={'CIK': str})
            cik_df.to_pickle(PICKLE_LOC_1)
        slice = cik_df.loc[cik_df['Ticker'] == user_args.stock, 'CIK']
        if slice.empty:
            sys.exit(
                'CIK not found with stock symbol: {}'.format(user_args.stock)
            )
        cik = slice.values[0]
    df = create_stock_table(cik, user_args.startdate, user_args.enddate)
    if user_args.html:
        with open(HTML_LOC, "w") as html_file:
            html = df.to_html(columns=SHOW_COLUMNS)
            html_file.write(html)
