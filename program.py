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

HTML_COLUMNS = [
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
parser.add_argument(
    '-p', '--position', type=str.lower, help="Restrict search by position e.g. CEO"
)
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
parser.add_argument(
    '--transaction-type', default='P-Purchase', metavar='Transaction',
    help="Specify what transaction type to parse on. Default is 'P-Purchase'."
)


def get_cik(user_args):
    """Get CIK either from user or from csv."""
    if user_args.cik:
        return user_args.cik
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
        return slice.values[0]


def create_stock_table(cik, user_args):
    if os.path.isfile(PICKLE_LOC_2):
        print('SEC pickle found')
        sec_df = pd.read_pickle(PICKLE_LOC_2)
        slice = sec_df.loc[
            (sec_df['CIK'] == cik)
            & (sec_df['Transaction Date'] >= user_args.startdate)
            & (sec_df['Transaction Date'] <= user_args.enddate)
        ]
    else:
        sec_df = None
        slice = pd.Series()
    if slice.empty:
        print('SEC not found; Begin querying')
        owners, trades = query_tables(cik, user_args)
        if not trades:
            return slice
        trade_df = pd.concat(trades, sort=False, ignore_index=True)
        trade_df['Position'] = trade_df.apply(
            lambda row: owners.get(row['Reporting Owner'], None), axis=1
        )
        trade_df['CIK'] = cik
        if sec_df is not None:
            sec_df = sec_df.append(trade_df)
        else:
            sec_df = trade_df
        (
            sec_df
            .drop_duplicates()
            .sort_values(by='Transaction Date')
            .reset_index(inplace=True)
        )
        sec_df.to_pickle(PICKLE_LOC_2)
    slice = sec_df.loc[
        (sec_df['CIK'] == cik)
        & (sec_df['Transaction Date'] >= user_args.startdate)
        & (sec_df['Transaction Date'] <= user_args.enddate)
    ]
    if user_args.position is not None and not slice.empty:
        return slice.loc[slice['Position'].str.contains(user_args.position)]
    return slice


def query(cik, page_num=0):
    url = 'https://www.sec.gov/cgi-bin/own-disp?action=getissuer&CIK={}'
    url = url.format(cik)
    if page_num:
        url += '&type=&dateb=&owner=include&start=0'.format(page_num)
    print(url)
    try:
        page = urlopen(url)
    except Exception as e:
        return None
    else:
        return page


def query_tables(cik, user_args):
    page = query(cik)
    soup = BeautifulSoup(page, 'html.parser')
    owners_table = soup.find(
        'table', {'border': 1, 'cellspacing': 0, 'cellpadding': 3}
    )
    rows = owners_table.find_all('tr')
    owners = {}
    trades = []
    print('Querying owners: ')
    for body, row in enumerate(rows):
        if not body:
            continue
        cells = row.find_all('td')
        owner = cells[0].find(text=True)
        filling = cells[1].find(text=True)
        position = cells[3].find(text=True)
        owners[owner] = position
        if user_args.position is None or user_args.position in position.lower():
            t = query_transactions(
                filling, user_args.startdate, user_args.transaction_type
            )
            trades.extend(t)
    print("querying company's transactions")
    t = query_transactions(cik, user_args.startdate, user_args.transaction_type)
    trades.extend(t)
    return owners, trades


def query_transactions(cik, startdate, transaction_type, page_num=0):
    trades = []
    last_transaction = datetime.datetime.now()
    while True:
        page = query(cik, page_num)
        if page is None:
            return trades
        else:
            page_num += 80
            soup = BeautifulSoup(page, 'html.parser')
            # Check if table is present
            table_attrs = {'id': 'transaction-report'}
            table = soup.find('table', attrs=table_attrs)
            if table is None or len(table.select('tr')) == 1:
                return trades
            trade_df = pd.read_html(soup.prettify(), attrs=table_attrs, header=0)[0]
            trade_df['Transaction Date'] = pd.to_datetime(
                trade_df['Transaction Date'], format="%Y-%m-%d"
            )
            last_transaction = min(trade_df['Transaction Date'])
            tdf = trade_df[trade_df['Transaction Type'] == transaction_type]
            if not tdf.empty:
                trades.append(tdf)
            if last_transaction < startdate:
                return trades


if __name__ == '__main__':
    sys.setrecursionlimit(1000000000)
    user_args = parser.parse_args()
    cik = get_cik(user_args)
    print('Using CIK {}'.format(cik))
    df = create_stock_table(cik, user_args)
    if user_args.html:
        if df.empty:
            sys.exit('No data matching parameters')
        else:
            print('Outputting html file: {}'.format(HTML_LOC))
            with open(HTML_LOC, "w") as html_file:
                html = df.to_html(columns=HTML_COLUMNS)
                html_file.write(html)
