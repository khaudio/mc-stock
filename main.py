#!/usr/bin/env python

"""
mc-stock checks stock on specified items at Microcenter store locations, and
sends email notifications when changes are detected.  Applicably, it helps
the user obtain rare items during shortages, like graphics cards.
"""

from aiohttp import ClientSession
from async_timeout import timeout
from getpass import getpass
from re import search
from smtplib import SMTP
import asyncio


class MCStock(object):
    def __init__(self, storeNum):
        self.storeNum = '131' if not storeNum else str(storeNum)


class Store(MCStock):
    def __init__(self, storeNum, server=None, port=None, sender=None, password=None, recipient=None, debug=False):
        super().__init__(storeNum)
        self.items, self.newInStock, self.totalInStock = set(), 0, 0
        self.debug = False if debug is None else debug # Setting debug to True enables false positives for testing
        self.server = 'smtp.gmail.com' if server is None else server
        self.port = 587 if port is None else port
        self.sender = input('Enter sender email address: ') if sender is None else sender
        if not self.sender:
            raise ValueError('Sender address cannot be empty')
        self.recipient = sender if recipient is None else recipient # Assumes loopback if recipient is not provided
        if self.server and self.sender and not password:
            self.__password = getpass('Enter email password: ')
        else:
            self.__password = password
        self.recipient = recipient
        self.loop = asyncio.get_event_loop()


    def __str__(self):
        return '\n'.join(item.__str__() for item in self.items)


    def __enter__(self):
        return self


    def __exit__(self, a, b, c):
        self.loop.close()


    def run(self, minutes=15):
        run = asyncio.ensure_future(self.check(minutes))
        self.loop.run_forever()


    async def check(self, minutes=15):
        assert isinstance(minutes, (int, float)), 'Minutes must be an integer or float'
        seconds = minutes * 60
        while True:
            print('Checking stock...')
            await self.update()
            if self.newInStock:
                print('New items available')
                if self.send_email(self.email_subject(), self.email_message()):
                    print('Recipient notified of stock changes')
            else:
                print('Stock unchanged')
            await asyncio.sleep(seconds)


    def add(self, *urls):
        for url in urls:
            assert isinstance(url, str), 'URL must be a string'
            if url not in (item.url for item in self.items):
                new = Item(self.storeNum, url)
                self.loop.run_until_complete(new.update())
                self.items.add(new)


    def remove(self, *urls):
        for url in urls:
            assert isinstance(url, str), 'URL must be a string'
        self.items = set(filter(lambda item: item.url not in urls, self.items))


    def email_message(self):
        if self.debug:
            new = self.items
        else:
            new = list(filter(lambda item: item.stockChanged, self.items))
        message = '\n'.join(item.__str__() for item in new)
        print(message)
        return message


    def email_subject(self):
        return f'({self.newInStock} new, {self.totalInStock} total) items in stock at Microcenter {self.storeNum}'


    def send_email(self, subject, message):
        server = SMTP(self.server, self.port)
        server.ehlo()
        server.starttls()
        server.login(self.sender, self.__password)
        body = '\n'.join([f'To: {self.recipient}', f'From: {self.sender}', f'Subject: {subject} ', '', message])
        try:
            server.sendmail(self.sender, self.recipient, body)
            sent = True
        except:
            sent = False
        server.quit()
        return sent


    async def update(self):
        for item in self.items:
            await item.update()
        if self.debug:
            self.newInStock, self.totalInStock = (len(self.items) for i in range(2))
        else:
            self.newInStock = sum(item.stockChanged for item in self.items)
            self.totalInStock = sum(item.stock for item in self.items)


class Item(MCStock):
    def __init__(self, storeNum, url):
        super().__init__(storeNum)
        self.url = url
        self.sku, self.price, self.stock, = (None for i in range(3))
        self.stockChanged, self.priceChanged = False, False
        self.loop = asyncio.get_event_loop()


    def __str__(self):
        stock = 'in' if self.stock else 'out of'
        return f'SKU {self.sku} is {stock} stock for {self.price} at Microcenter {self.storeNum}\n{self.url}\n'


    async def pull(self):
        async with ClientSession() as session:
            async with timeout(10):
                async with session.get(self.url, params={'storeSelected': self.storeNum}) as response:
                    return await response.text()


    @staticmethod
    def parse_lines(page):
        for var in ['SKU', 'inStock', 'productPrice']:
            reply = search(f"(?<='{var}':').*?(?=',)", page)
            if reply:
                yield reply.group()


    @staticmethod
    def compare(new, old):
        return True if new != old and old is not None else False


    async def update(self):
        data = tuple(self.parse_lines(await self.pull()))
        if not data or any(data) is None:
            raise ValueError('Data missing from request or store number invalid')
        self.sku, stock, price = int(data[0]), data[1] is 'True', float(data[2])
        self.stockChanged, self.priceChanged = self.compare(stock, self.stock), self.compare(price, self.price)
        self.stock, self.price = stock, price


if __name__ == '__main__':
    rx570 = [
        'http://www.microcenter.com/product/478850/Radeon_RX-570_ROG_Overclocked_4GB_GDDR5_Video_Card',
        'http://www.microcenter.com/product/478907/Radeon_RX_570_Overclocked_4GB_GDDR5_Video_Card'
        ]

    with Store(131) as store:
        store.add(*rx570)
        store.run()
