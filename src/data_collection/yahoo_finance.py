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