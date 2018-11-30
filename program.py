import argparse
import csv
import os
import sqlite3


parser = argparse.ArgumentParser()

def connect(sqlite_file):
    """Make connection to an SQLite database file """
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    return conn, c


def does_table_exist(c, table_name):
    query = "SELECT name FROM sqlite_master"
    query += " WHERE type='table' AND name='{}';".format(table_name)
    c.execute(query)
    return bool(c.fetchall())


def create_cik_table(c, table_name):
    with open('/Users/alexfeldman/CS/Freelance/Stocks/cik-data/cik.csv', 'r') as f:
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


if __name__ == '__main__':
    sqlite_file = '/Users/alexfeldman/CS/Freelance/Stocks/my_first_db.sqlite'
    cik_table = 'cik'
    conn, c = connect(sqlite_file)
    if not does_table_exist(c, cik_table):
        create_cik_table(c, cik_table)
    conn.close()

    "https://www.sec.gov/cgi-bin/own-disp?action=getissuer&CIK=0000051143"
