# SEC-information-tables

## Requirements

This script needs [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) to run. The command below in your virtualenv to install.
```
$ pip install beautifulsoup4
```

## Running

```
$ python program.py -h
usage: program.py [-h] [-c CIK] [-s [Date]] [-e [Date]] [--sql [Path]]
                  [--cikpath [Path]] [-html]
                  stock

positional arguments:
  stock                 Stock symbol e.g. AAL, AAPL

optional arguments:
  -h, --help            show this help message and exit
  -c CIK, --cik CIK     Company's CIK identifier
  -s [Date], --startdate [Date]
                        Choose a start date in format YYYY-MM-DD. Default is
                        30 days prior.
  -e [Date], --enddate [Date]
                        Choose a start date in format YYYY-MM-DD. Default is today.
  --sql [Path]          Path to sqlite database. Default is location is this directory + sec.db
  --cikpath [Path]      Path to cik.csv. Default location is this directory + cik.csv
  --html                Return sql to html table.
  ```
