# SEC-information-tables

## Requirements

This script needs [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/), [Pandas](https://pandas.pydata.org/), and [lxml](https://lxml.de/) to run
```
$ pip install beautifulsoup4
$ pip install pandas
$ pip install lxml
```

## Running
The Behavior of the script is can be broken down into a few parts:
1. First fetch the CIK data from the user parameters or from `cik.csv`.
2. Query the [SEC Edgar](https://www.sec.gov) site based on parameters. Default parameters are `P-Purchase` transactions within previous year.
3. Return an html table (`--html`) with data found in parameters, an `.html` is created. If no data is found, message indicating situation is printed.
4. Headers can be dynamically sorted. More info about that [here](https://mottie.github.io/tablesorter/docs/)

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
    --html                Return data to html table.
    -p POSITION, --position POSITION
                          Restrict search by position e.g. CEO
    -s [Date], --startdate [Date]
                          Choose a start date in format YYYY-MM-DD. Default is 1
                          year prior.
    -e [Date], --enddate [Date]
                          Choose a start date in format YYYY-MM-DD. Default is
                          today.
    --cikpath [Path]      Path to cik.csv. Default location is
                          /.../.../.../.../.../cik.csv
    --transaction-type Transaction
                          Specify what transaction type to parse on. Default is
                          'P-Purchase'.
  ```
