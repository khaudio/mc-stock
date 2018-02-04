#!/usr/bin/env python3

import re
import requests
from time import sleep
import smtplib
try:
    import cPickle as pickle
except:
    import pickle
import os


storeNumber = '131'
cookies = {'storeSelected': storeNumber}
global inStockItems
itemURLs = []
global msgText
msgText = ""
stockCurrent = {}
if os.path.exists("items_in_stock"):
    stockLast = pickle.load(open(r"items_in_stock", "rb"))

class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        return self.set_current - self.intersect
    def removed(self):
        return self.set_past - self.intersect
    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])

rx570 = [
   'http://www.microcenter.com/product/478850/Radeon_RX-570_ROG_Overclocked_4GB_GDDR5_Video_Card',
   'http://www.microcenter.com/product/478907/Radeon_RX_570_Overclocked_4GB_GDDR5_Video_Card',
   'http://www.microcenter.com/product/478810/Radeon_RX-570_Overclocked_4GB_GDDR5_Video_Card',
   'http://www.microcenter.com/product/478364/Radeon_RX_570_GAMING_X_4GB_GDDR5_Video_Card',
   'http://www.microcenter.com/product/478668/Radeon_RX_570_Gaming_4GB_GDDR5_Video_Card',
   'http://www.microcenter.com/product/478683/Radeon_NITRO_RX_570_Overclocked_8GB_GDDR5_Video_Card'
    ]

rx580= [
    'http://www.microcenter.com/product/478666/Radeon_RX_580_Gaming_4GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/478363/Radeon_RX_580_ARMOR_Overclocked_4GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/479406/Radeon_RX_580_Overclocked_4GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/479279/Radeon_RX_580_Overclocked_8GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/478664/Radeon_RX_580_Gaming_8GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/478662/AORUS_Radeon_RX_580_XTR_8GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/478663/AORUS_Radeon_RX_580_8GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/479526/Red_Dragon_Radeon_RX-580_Overclocked_4GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/478360/Radeon_RX_580_GAMING_X_8GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/478682/Radeon_Pulse_RX_580_Overclocked_4GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/478700/AXRX_Radeon_RX-580_Red_Devil_8GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/478905/Radeon_RX_580_Overclocked_8GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/478802/Radeon_RX-580_Overclocked_8GB_GDDR5_Graphics_Card',
    'http://www.microcenter.com/product/478849/Radeon_RX-580_ROG_Overclocked_8GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/478362/Radeon_RX_580_GAMING_X_4GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/478665/AORUS_Radeon_RX_580_4GB_GDDR5_Video_Card',
    'http://www.microcenter.com/product/478701/AXRX_Radeon_RX-580_Red_Devil_Overclocked_8GB_GDDR5_Video_Card'
    ]

for item in rx570:
    respData = requests.get(item, cookies=cookies).text
    skuNum = re.findall(r'SKU:"(.*?)",',str(respData))
    inStock = re.findall(r'inStock:"(.*?)",',str(respData))
    productPrice = re.findall(r'price:"(.*?)",',str(respData))
    storeId = re.findall(r'storeId:"(.*?)",',str(respData))
    stockCurrent[skuNum[0]] = inStock[0]
    for stock in inStock:
        if stock == "True":
            msgText = msgText+"RX 570 -- SKU: "+skuNum[0]+" -- "+productPrice[0]+"\n"+item+"\n\n"
        elif stock == "False":
            print("RX 570 -- SKU: "+skuNum[0]+" -- Out of stock")
        else:
            print("Error retrieving stock")
    sleep(5)

for item in rx580:
    respData = requests.get(item, cookies=cookies).text
    skuNum = re.findall(r'SKU:"(.*?)",',str(respData))
    inStock = re.findall(r'inStock:"(.*?)",',str(respData))
    productPrice = re.findall(r'price:"(.*?)",',str(respData))
    storeId = re.findall(r'storeId:"(.*?)",',str(respData))
    stockCurrent[skuNum[0]] = inStock[0]
    for stock in inStock:
        if stock == "True":
            msgText = msgText+"RX 580 -- SKU: "+skuNum[0]+" -- "+productPrice[0]+"\n"+item+"\n\n"
        elif stock == "False":
            print("RX 580 -- SKU: "+skuNum[0]+" -- Out of stock")
        else:
            print("Error retrieving stock")
    sleep(5)

with open(r"items_in_stock", "wb") as outfile:
    pickle.dump(stockCurrent, outfile)

stockDiff = DictDiffer(stockCurrent, stockLast).changed()

if stockDiff:
    print("Stock changed:")
    for i in stockDiff:
        if stockCurrent[i] == "False":
            print(i+" -- "+"Out of stock")
        elif stockCurrent[i] == "True":
            print(i+" -- "+"IN STOCK")
else:
    print("Stock unchanged")

storeInfo="""Paste store address and other info here"""

if len(msgText) and stockDiff:
    print(msgText)
    TO = ['YourOwnEmail@whatever.com']
    SUBJECT = 'GPU IN STOCK at Microcenter'
    TEXT = msgText+"\n\n"+storeInfo

    # Gmail Sign In
    gmail_sender = 'YourServerEmail@gmail.com'
    gmail_passwd = 'YourServerEmailPW'

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(gmail_sender, gmail_passwd)

    BODY = '\r\n'.join(['To: %s' % TO,
                        'From: %s' % gmail_sender,
                        'Subject: %s' % SUBJECT,
                        '', TEXT])

    try:
        server.sendmail(gmail_sender, TO, BODY)
        print ('Email sent')
    except:
        print ('Error sending mail')

    server.quit()
else:
    print("No email sent")
del inStock,msgText
