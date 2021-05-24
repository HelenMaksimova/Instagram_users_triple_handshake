from urllib.parse import urljoin
from scrapy import Selector
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose
from .items import InstFollowerItem, InstFollowingItem


class InstFollowerLoader(ItemLoader):
    default_item_class = InstFollowerItem
    username_out = TakeFirst()
    parent_out = TakeFirst()
    user_type_out = TakeFirst()


class InstFollowingLoader(ItemLoader):
    default_item_class = InstFollowingItem
    username_out = TakeFirst()
    parent_out = TakeFirst()
    user_type_out = TakeFirst()
