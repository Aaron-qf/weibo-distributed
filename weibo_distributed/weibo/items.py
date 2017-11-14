# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class UserItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    id = scrapy.Field()
    image = scrapy.Field()
    name = scrapy.Field()
    cover = scrapy.Field()
    description = scrapy.Field()
    follows_count = scrapy.Field()
    fans_count = scrapy.Field()
    gender = scrapy.Field()
    statuses_count = scrapy.Field()
    verified = scrapy.Field()
    verified_reason = scrapy.Field()
    verified_type = scrapy.Field()
    flag = scrapy.Field()

    pass

class WeiboItem(scrapy.Item):
    id = scrapy.Field()
    attitudes_count = scrapy.Field()
    comments_count = scrapy.Field()
    reposts_count = scrapy.Field()
    text = scrapy.Field()
    raw_text = scrapy.Field()
    text_length = scrapy.Field()
    thumbnail_picture = scrapy.Field()
    pictures = scrapy.Field()
    user = scrapy.Field()
    source = scrapy.Field()
    is_long_text = scrapy.Field()
    created_at = scrapy.Field()
    origin = scrapy.Field()
    pid = scrapy.Field()
    keyword = scrapy.Field()
