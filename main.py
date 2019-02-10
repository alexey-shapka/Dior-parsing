from scrapy import Request, Field, Spider, Item
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.log import configure_logging
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.spiders import Rule
import pandas as pd
import datetime
import json
import csv
import re

class Product(Item):
    url = Field()
    name = Field()
    price = Field()
    currency = Field()
    category = Field()
    sku = Field()
    availability = Field()
    time = Field()
    color = Field()
    size = Field()
    region = Field()
    description = Field()

class DiorSpider(Spider):
    name = 'dior'
    def __init__(self, *args,**kwargs):
        self.allowed_domains = ['dior.com']
        self.start_urls = ['https://www.dior.com/en_us', 'https://www.dior.com/fr_fr']
        self.outputFile = open("result.csv", "w", newline="")
        self.headers = ['url', 'name', 'price', 'currency','category', 'sku', 'availability',
                         'time', 'color', 'size', 'region', 'description']
        self.writer = csv.DictWriter(self.outputFile, fieldnames=self.headers)
        self.writer.writeheader()
        self.unique_data = set()
        self.rules = (Rule(LinkExtractor(allow=('dior.com/en_us')), callback='parse'),
                      Rule(LinkExtractor(allow=('dior.com/fr_fr')), callback='parse'))

    def parse(self, response):
        #get all categories
        Links = []
        for link in response.xpath('//div[@class="navigation-items"]/ul//@href').extract():
            if '.html' not in link:
                Links.append(link)

        for link in Links:
            yield  Request('https://www.dior.com' + link, callback = self.ProductLinks)

    def ProductLinks(self, response):
        #get all products
        Links = response.xpath('//a[@class="product-link"]//@href').extract()
        for link in Links:
            yield  Request('https://www.dior.com' + link.encode('ascii', 'ignore').decode(), callback = self.GetProductInformation)

    def GetProductInformation(self, response):
        Scripts = response.xpath('/html').extract()
        #find value of dataLayer var in scripts
        FirstScript = re.search(r'var dataLayer = .*;', Scripts[0]).group().encode('ascii', 'ignore').decode()
        #find script with all colors and sizes
        SecondScript = re.search(r'window.initialState = .*', Scripts[0]).group().encode('ascii', 'ignore').decode()

        #if scripts not null
        try:
            obj1 = json.loads(FirstScript[FirstScript.find('[')+1:-2])
            obj2 = json.loads(SecondScript[SecondScript.find('=')+2:])
            var = {}

            #find dict with necessary key
            for i in obj2['CONTENT']['cmsContent']['elements']:
                if 'variations' in i:
                    var = i
                    break

            #check on variations
            try:
                Variations = var['variations']
                for i in Variations: 
                    item = Product()
                    item['url'] = obj1['page'].encode('ascii', 'ignore').decode()
                    item['name'] = obj1['ecommerce']['detail']['products']['name'].encode('ascii', 'ignore').decode()
                    item['price'] = i['price']['value']
                    item['currency'] = i['price']['currency']
                    item['category'] = obj1['ecommerce']['detail']['products']['category']
                    item['sku'] = i['sku']
                    item['time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    item['availability'] = i['status']
                    item['region'] = obj1['country']
                    item['description'] = ' '.join(response.xpath('//div[@class="product-tab-html"]/text()').extract()).replace('\n', '').replace('\r', '').encode('ascii', 'ignore').decode()
                    #if parameters don`t exist set ''
                    try:
                        item['color']  = i['tracking'][0]['ecommerce']['add']['products']['variant']
                        item['size'] = i['title']
                    except:
                        item['size'] = ''
                        item['color'] = ''

                    #check on duplicate
                    if item['sku'] and (item['sku'] not in self.unique_data):
                        self.unique_data.add(item['sku'])
                    self.writer.writerow(item)
                    yield item

            #if one variant - get data from datalayer
            except:
                item = Product()
                item['url'] = obj1['page'].encode('ascii', 'ignore').decode()
                item['name'] = obj1['ecommerce']['detail']['products']['name'].encode('ascii', 'ignore').decode()
                item['price'] = obj1['ecommerce']['detail']['products']['price']
                item['currency'] = obj1['ecommerce']['currencyCode']
                item['category'] = obj1['ecommerce']['detail']['products']['category']
                item['sku'] = obj1['ecommerce']['detail']['products']['dimension16']
                item['time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                item['availability'] = obj1['ecommerce']['detail']['products']['dimension25']
                item['region'] = obj1['country']
                item['description'] = ' '.join(response.xpath('//div[@class="product-tab-html"]/text()').extract()).replace('\n', '').replace('\r', '').encode('ascii', 'ignore').decode()
                item['color'] = obj1['ecommerce']['detail']['products']['variant']
                item['size'] = ''

                #check on duplicate
                if item['sku'] and (item['sku'] not in self.unique_data):
                    self.unique_data.add(item['sku'])
                    self.writer.writerow(item)
                    yield item

        #if var dataLayer empty, find another json
        except:
            FirstScript = re.search(r'c_myLadyDiorApp.push.*;', Scripts[0]).group().encode('ascii', 'ignore').decode()[21:-2]
            #add double quotes for convert string in json
            FirstScript = FirstScript.replace('description: "" ,data: ', '\"description\":\"\", \"data\":').replace('routes', '\"routes\"').replace('wording', '\"wording\"').replace('config', '\"config\"').replace('baseUrl', '\"baseUrl\"').replace('location', '\"location\"').replace('contactUrl', '\"contactUrl\"').replace('mobile', '\"mobile\"').replace('isEcommerce', '\"isEcommerce\"').replace('trackingKeys: {"0":{"events":["dior.click"],', '\"trackingKeys\": {"0":{"events":["dior.click"],')
            obj = json.loads(FirstScript)
            
            for i in obj['data']['step2']['colors']['items']:
                item = Product()
                item['url'] = obj['baseUrl'] +'/' + i['url']
                item['name'] = i['name']
                item['price'] = i['price']
                item['currency'] = i['trackingKeys']['0']['ecommerce']['currencyCode']
                item['category'] = i['trackingKeys']['0']['ecommerce']['click']['products']['category']
                item['sku'] = i['trackingKeys']['0']['ecommerce']['click']['products']['dimension16']
                item['availability'] = i['trackingKeys']['0']['ecommerce']['click']['products']['dimension25']
                item['time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                item['color'] = i['trackingKeys']['0']['ecommerce']['click']['products']['variant']
                item['size'] = ''
                item['region'] = i['trackingKeys']['country']
                item['description'] = ' '.join(i['caracteristics'])

                if item['sku'] and (item['sku'] not in self.unique_data):
                    self.unique_data.add(item['sku'])
                    self.writer.writerow(item)
                    yield item

configure_logging()
runner = CrawlerRunner()

@defer.inlineCallbacks
def crawl():
    yield runner.crawl(DiorSpider)
    reactor.stop()

crawl() 
reactor.run()