#/usr/bin/env python

"""
mc-stock checks stock on specified items at Microcenter store locations, and
sends email notifications when changes are detected.  Applicably, it helps
the user obtain rare items during shortages, like graphics cards.
"""


from getpass import getpass
from multiprocessing import cpu_count, Pool, Queue
from re import search
from requests import get
from time import sleep
from smtplib import SMTP


class MCStock(object):
    def __init__(self, storeNum):
        self.storeNum = '131' if not storeNum else str(storeNum)


class Store(MCStock):
    def __init__(self, storeNum, server=None, port=None, sender=None, password=None, recipient=None, debug=False):
        super().__init__(storeNum)
        self.items = set()
        self.newInStock, self.totalInStock = 0, 0
        self.debug = False if debug is None else debug # Setting debug to True enables false positives for testing
        self.server = 'smtp.gmail.com' if server is None else server
        self.port = 587 if port is None else port
        self.sender = input('Enter sender email address: ') if sender is None else sender
        if not self.sender:
            raise ValueError('Sender address cannot be empty')
        self.recipient = sender if recipient is None else recipient # Assumes loopback if recipient is not provided
        if self.server and self.sender and not password:
            self.password = getpass('Enter email password: ')
        else:
            self.password = password
        self.recipient = recipient


    def __str__(self):
        return '\n'.join(item.__str__() for item in self.items)


    def add(self, *links):
        for link in links:
            if isinstance(link, (list, tuple, set)):
                for l in link:
                    self.add_link(l)
            elif isinstance(link, str):
                self.add_link(link)
            else:
                raise TypeError('Links must be a string or list of strings')


    def add_link(self, link):
        if isinstance(link, str):
            if link not in (item.link for item in self.items):
                new = Item(self.storeNum, link)
                new.update()
                self.items.add(new)
        else:
            raise TypeError('Link must be a string')


    def remove(self, links):
        for link in links:
            for item in self.items:
                if link == item.link:
                    self.items.remove(item)


    def email_message(self, q):
        new = []
        while not q.empty():
            new.append(q.get())
        message = '\n'.join(item.__str__() for item in new)
        return message


    def email_subject(self):
        return f'({self.newInStock} new, {self.totalInStock} total) items in stock at Microcenter {self.storeNum}'


    def send_email(self, subject, message):
        server = SMTP(self.server, self.port)
        server.ehlo()
        server.starttls()
        server.login(self.sender, self.password)
        body = '\n'.join([f'To: {self.recipient}',
                            f'From: {self.sender}',
                            f'Subject: {subject}'
                            '', message])
        try:
            server.sendmail(self.sender, self.recipient, body)
            sent = True
        except:
            sent = False
        server.quit()
        return sent


    def update(self):
        q = Queue()
        p = Pool(cpu_count())
        for item in p.imap(self.update_item, self.items):
            q.put(item)
        self.newInStock = q.qsize()
        self.totalInStock = sum(item.stock for item in self.items)
        return q


    def run(self, minutes=15):
        if isinstance(minutes, int):
            seconds = minutes * 60
        else:
            raise TypeError('Minutes must be an integer or float')
        while True:
            q = self.update()
            subject = self.email_subject()
            message = self.email_message(q)
            if self.newInStock:
                if self.send_email(subject, message):
                    print('Recipient notified of stock changes')
            sleep(seconds)


    def update_item(self, item):
        item.update()
        if item.stock and item.stockChanged or self.debug:
            return item


class Item(MCStock):
    def __init__(self, storeNum, link):
        super().__init__(storeNum)
        self.link = link
        self.sku = None
        self.price = None
        self.stock = None
        self.stockChanged = False
        self.priceChanged = False


    def __str__(self):
        if self.stock:
            stock = 'in stock'
        else:
            stock = 'out of stock'
        return f'SKU {self.sku} is {stock} for {self.price} at Microcenter {self.storeNum}\n{self.link}\n'


    def pull(self):
        page = get(self.link, cookies={'storeSelected': self.storeNum}).text
        return page


    def parse_lines(self, page):
        for var in ['SKU', 'inStock', 'productPrice']:
            reply = search(f"(?<='{var}':').*?(?=',)", page)
            if reply:
                yield reply.group()


    def update(self):
        page = str(self.pull())
        data = tuple(self.parse_lines(page))
        if not data or any(data) is None:
            raise ValueError('Data missing from request or store number invalid')
        self.sku, inStock, price = int(data[0]), data[1], float(data[2])
        if inStock == 'True':
            stock = True
        else:
            stock = False
        if stock != self.stock and self.stock is not None:
            self.stockChanged = True
        else:
            self.stockChanged = False
        if price != self.price and self.price is not None:
            self.priceChanged = True
        else:
            self.priceChanged = False
        self.stock = stock
        self.price = price

if __name__ == '__main__':
    rx570 = ['http://www.microcenter.com/product/478850/Radeon_RX-570_ROG_Overclocked_4GB_GDDR5_Video_Card',
             'http://www.microcenter.com/product/478907/Radeon_RX_570_Overclocked_4GB_GDDR5_Video_Card']
    mc = Store(131)
    mc.add(rx570)
    mc.run()
