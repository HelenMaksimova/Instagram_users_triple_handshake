# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstagramUserItem(scrapy.Item):
    _id = scrapy.Field()
    parent = scrapy.Field()
    username = scrapy.Field()
    user_type = scrapy.Field()


class InstFollowerItem(InstagramUserItem):
    pass


class InstFollowingItem(InstagramUserItem):
    pass
