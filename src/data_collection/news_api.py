# src/data_collection/news_api.py

import requests

class NewsAPIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://newsapi.org/v2/'

    def get_top_headlines(self, country='us', category='business', page_size=10):
        url = f'{self.base_url}top-headlines'
        params = {
            'country': country,
            'category': category,
            'pageSize': page_size,
            'apiKey': self.api_key
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return None