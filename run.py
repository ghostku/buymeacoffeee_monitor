import requests
import json
import logging as log
import os

from bs4 import BeautifulSoup
from json import JSONDecodeError

URL = 'https://buymeacoffee.com/vkv_official'
URL_PATTERN = 'https://buymeacoffee.com/vkv_official/'
EXCLUDE_URLS = ['https://buymeacoffee.com/vkv_official/membership', 'https://buymeacoffee.com/vkv_official/posts', 'https://buymeacoffee.com/vkv_official/extras/checkout/0']
POSTS_FILE = 'posts.json'


class TelergamError(Exception):
    pass


class VKVMonitor():
    def __init__(self) -> None:
        self.chat_id = os.environ.get('CHAT_ID')
        self.token = os.environ.get('TOKEN')

    def send_message(self, message: str):
        url = f'https://api.telegram.org/bot{self.token}/sendMessage'

        params = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'Markdown',
        }

        response = requests.get(url, params=params)
        if not response.status_code == 200:
            raise TelergamError(response.json())

    def process_new_post(self, url: str, posts: dict) -> dict:
        soup = BeautifulSoup(requests.get(url).content, 'html.parser')
        title = soup.find('h1').get_text()
        record = {'title': title, 'url': url}

        log.info('Save to POSTS')
        posts[url] = record
        json.dump(posts, open(POSTS_FILE, 'w'))
        log.info('Send notification')
        message = f'Новий пост від ВКВ: \n\n[{title}]({url})'
        self.send_message(message)
        return posts

    def process(self):
        message = 'Запустили чудо моніторинг постів від ВКВ на buymeacoffee'
        log.info(message)
        # self.send_message(message)
        try:
            posts = json.load(open(POSTS_FILE))
        except (FileNotFoundError, JSONDecodeError):
            posts = {}


        # Step 1: Get info from webpage
        response = requests.get(URL)

        # Step 2: Parse the webpage
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a')
        links = [link.get('href') for link in links]
        links = [link for link in links if link]
        links = [link for link in links if link.startswith(URL_PATTERN)]
        links = [link for link in links if not link in EXCLUDE_URLS]

        for link in links:
            if link not in posts:
                posts = self.process_new_post(link, posts)

if __name__ == '__main__':
    monitor = VKVMonitor()
    monitor.process()