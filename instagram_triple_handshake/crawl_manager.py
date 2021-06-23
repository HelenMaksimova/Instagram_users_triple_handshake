import os
import dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from instagram_triple_handshake.spiders.instagram_user import InstagramUserSpider
from sys import argv
import json

_, user_names, coil = argv
dotenv.load_dotenv(".env")
crawler_settings = Settings()
crawler_settings.setmodule("instagram_triple_handshake.settings")
crawler_process = CrawlerProcess(settings=crawler_settings)
crawler_process.crawl(
    InstagramUserSpider,
    login=os.getenv("INST_LOGIN"),
    password=os.getenv("INST_PASSWD"),
    user_names=json.loads(user_names),
    coil=int(coil)
)
crawler_process.start()
