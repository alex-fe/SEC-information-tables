# SEC-information-tables

## Requirements

This script needs [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) and [Pandas](https://pandas.pydata.org/) to run
```
$ pip install beautifulsoup4
$ pip install pandas
```

## Running
The Behavior of the script is can be broken down into a few parts:
1. First fetch the CIK data from the user parameters or from `cik.csv`. If getting from `cik.csv`, pickle the dataframe for faster future queries. 
2. Search the pickled SEC DataFrame based on parameters (cik, start date, end date, position) for `P-Purchase` transactions. If unable to find the data based on parameters, query the [SEC Edgar](https://www.sec.gov) site, adding the pulled data to the pickle.
3. Return an html table (`--html`) with data found in parameters, an `.html` is created. If no data is found, message indicating situation is printed.

E.G for querying Forward Industries Inc
```
$ python program.py FORD --html
```

Full argument parameters listed below

```
$ python program.py -h
usage: program.py [-h] [-c CIK] [--html] [-p POSITION] [-s [Date]] [-e [Date]]
                  [--cikpath [Path]]
                  stock

positional arguments:
  stock                 Stock symbol e.g. AAL, AAPL

optional arguments:
  -h, --help            show this help message and exit
  -c CIK, --cik CIK     Company's CIK identifier
  --html                Return sql to html table.
  -p POSITION, --position POSITION
                        Restrict search by position e.g. CEO
  -s [Date], --startdate [Date]
                        Choose a start date in format YYYY-MM-DD. Default is
                        30 days prior.
  -e [Date], --enddate [Date]
                        Choose a start date in format YYYY-MM-DD. Default is
                        today.
  --cikpath [Path]      Path to cik.csv. Default location is
                        /.../.../.../.../.../cik.csv
  ```
