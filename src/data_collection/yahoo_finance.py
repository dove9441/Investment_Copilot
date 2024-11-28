# src/data_collection/yahoo_finance.py

import yfinance as yf

class YahooFinance:
    def __init__(self):
        pass

    def get_stock_data(self, ticker, period='1d', interval='1d'):
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        return hist


    def get_market_summary(self, indices=['^GSPC', '^DJI', '^IXIC']):
        data = {}
        for index in indices:
            ticker = yf.Ticker(index)
            info = ticker.info
            data[index] = {
                'name': info.get('shortName', ''),
                'price': info.get('regularMarketPrice', 0),
                'change': info.get('regularMarketChangePercent', 0)
            }
        return data


#get_stock_data
"""
Date                Open      High       Low     Close    Volume  Dividends  Stock Splits
2023-11-18 00:00:00  185.82  186.03    184.21   185.27  12345678        0.0           0.0_summary_
"""



#
"""
{
    '^GSPC': {
        'name': 'S&P 500',
        'price': 4514.02,
        'change': 1.2345
    },
    '^DJI': {
        'name': 'Dow Jones Industrial Average',
        'price': 35000.76,
        'change': 0.9876
    },
    '^IXIC': {
        'name': 'NASDAQ Composite',
        'price': 14058.87,
        'change': 1.5432
    }
}

"""