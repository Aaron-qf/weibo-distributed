# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo,re,time,datetime

from weibo.items import UserItem, WeiboItem

from py2neo.ogm import GraphObject, Property, RelatedTo, RelatedFrom, Related

from py2neo import Graph,Node,Relationship

#
# class WeiboPipeline(object):
#     def process_item(self, item, spider):
#         return item


class TimePipeline():
    def process_item(self, item, spider):
        if isinstance(item, UserItem) or isinstance(item, WeiboItem):
            now = time.strftime('%Y-%m-%d %H:%M', time.localtime())
            item['crawled_at'] = now
        return item


class WeiboPipeline():
    def parse_time(self, date):
        if re.match('刚刚', date):
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))
        if re.match('\d+分钟前', date):
            minute = re.match('(\d+)', date).group(1)
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time() - float(minute) * 60))
        if re.match('\d+小时前', date):
            hour = re.match('(\d+)', date).group(1)
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time() - float(hour) * 60 * 60))
        if re.match('昨天.*', date):
            date = re.match('昨天(.*)', date).group(1).strip()
            date = time.strftime('%Y-%m-%d', time.localtime(time.time()-24 * 60 * 60)) + ' ' + date
        if re.match('\d{2}-\d{2}', date):
            date = time.strftime('%Y-', time.localtime()) + date + ' 00:00'
        else:
            FORMAT = '%a %b %d %H:%M:%S +0800 %Y'
            date = datetime.datetime.strptime(date, FORMAT)
        return date

    def process_item(self, item, spider):
        if isinstance(item, WeiboItem):
            if item.get('created_at'):
                item['created_at'] = item['created_at'].strip()
                item['created_at'] = self.parse_time(item.get('created_at'))
            # if item.get('pictures'):
            #     item['pictures'] = [pic.get('url') for pic in item.get('pictures')]
        return item


class MongoPipeline(object):

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_url = mongo_uri
        self.mongo_db  = mongo_db

    @classmethod
    def from_crawler(cls,crawler):
        return cls(
            mongo_uri = crawler.settings.get('MONGO_URI'),
            mongo_db = crawler.settings.get('MONGO_DB')
        )

    def open_spider(self,spider):
        self.client = pymongo.MongoClient(self.mongo_url)
        self.db = self.client[self.mongo_db]
        self.db.userInfo.create_index([('id', pymongo.ASCENDING)])
        self.db.weiboInfo.create_index([('id', pymongo.ASCENDING)])

    def process_item(self, item, spider):
        if isinstance(item, UserItem):
            self.db.userInfo.update({'id': item.get('id')}, {'$set': item}, True)
        if isinstance(item, WeiboItem):
            self.db.weiboInfo.update({'id': item.get('id')}, {'$set': item}, True)
        return item



    def close_spider(self,spider):
        self.client.close()

class User(GraphObject):
    __primarykey__ = 'id'

    id = Property()
    image = Property()
    name = Property()
    cover = Property()
    description = Property()
    follows_count = Property()
    fans_count = Property()
    gender = Property()
    statuses_count = Property()
    verified = Property()
    verified_reason = Property()
    verified_type = Property()
    flag = Property()
    publish = Related('Weibo','PUBLISH')

class Weibo(GraphObject):
    __primarykey__ = 'id'

    id = Property()
    attitudes_count = Property()
    comments_count = Property()
    reposts_count = Property()
    text = Property()
    raw_text = Property()
    text_length = Property()
    thumbnail_picture = Property()
    pictures = Property()
    user = Property()
    source = Property()
    is_long_text = Property()
    created_at = Property()
    origin = Property()
    pid = Property()
    keyword = Property()

    repost = RelatedTo('Weibo','REPOST')
    publish = Related('User','PUBLISH')

class NeoPipeline(object):

    # graph = Graph(password = '222')#默认为本地连接
    graph = Graph(
        "bolt://114.215.100.72:7687",
        username="neo4j",
        password="buaacse123"
    )

    def process_item(self,item,spider):


        if isinstance(item,WeiboItem):
            weibo = Weibo()

            weibo.id = item['id']
            weibo.attitudes_count = item['attitudes_count']
            weibo.comments_count = item['comments_count']
            weibo.reposts_count = item['reposts_count']
            weibo.text = item['text']
            weibo.raw_text = item['raw_text']
            weibo.text_length = item['text_length']
            weibo.thumbnail_picture = item['thumbnail_picture']
            weibo.pictures =  item['pictures']
            weibo.user = item['user']
            weibo.source = item['source']
            weibo.is_long_text = item['is_long_text']
            weibo.created_at = item['created_at']
            weibo.origin = item['origin']
            weibo.pid = item['pid']
            weibo.keyword = item['keyword']


            # self.graph.create(weibo)#插入微博节点

            user = User.select(self.graph).where(id=item['user']).first()
            print('user------------------\n',user)
            user.publish.add(weibo)  # 通过发布关系插入微博节点（做到同时插入微博节点和相应的发布无向边）,如果不存在则添加，存在则更新
            self.graph.push(user)#更新数据库
            # self.graph.push(weibo)

            # if item['pid'] == str(0) and Weibo.select(self.graph).where(id=item['id']).first() == None:  # 表示根微博（？是否需要查找存在与否）
            if item['pid'] == 0 :  # 表示根微博（？是否需要查找存在与否）
                pass
            # elif item['pid']=='' and Weibo.select(self.graph).where(id=item['id']).first() == None:  # 最内层直接转发的微博
            elif item['pid']==None :  # 最内层直接转发的微博
                #方案二：
                # root_weibo = Weibo.select(self.graph).where(id=item['origin']).first()#获取根微博
                # repost_relationship =Relationship(dict(weibo),'REPOST',dict(root_weibo))#转发关系
                # self.graph.create(repost_relationship)#插入转发关系边到数据库

                #方案一
                # print('666666666666666666666666666666666\n\n\n')
                # print('-------------------origin\n\n',item['origin'],type(item['origin']))

                root_weibo = Weibo.select(self.graph).where(id=str(item['origin'])).first()  # 获取根微博

                print('-------------------root_weibo\n\n',root_weibo)
                weibo = Weibo.select(self.graph).where(id=item['id']).first()#获取刚刚插入的最内层微博
                weibo.repost.add(root_weibo)  # 建立和根微博的关系（有向边）
                self.graph.push(weibo)
            # elif item['pid']!=str(0) and item['pid']!='' and Weibo.select(self.graph).where(id=item['id']).first() == None: #最外层以及中间层微博
            elif item['pid']!=0 and item['pid']!=None : #最外层以及中间层微博

                #方案一
                print('77777777777777777777777\n\n\n')

                next_weibo = Weibo()#预先插入下一层转发微博id
                next_weibo.id = str(item['pid'])#下一层id=本层pid
                weibo = Weibo.select(self.graph).where(id=item['id']).first()#获取刚刚插入的最外层微博
                weibo.repost.add(next_weibo)#建立和转发下一层微博的关系（有向边），并预插入id
                self.graph.push(weibo)#？和之前插入微博节点重复，更新两次，可优化

                #优化方案二如下：不利用ogm
                # next_weibo = Weibo()  # 预先插入下一层转发微博id
                # next_weibo.id = item['pid']  # 下一层id=本层pid
                # weibo = Weibo.select(self.graph).where(id=item['id']).first()  # 获取刚刚插入的最外层微博
                # w= dict(weibo)
                # ww=dict(next_weibo)
                # repost_relationship = Relationship(w, 'REPOST',ww )  # 转发关系
                # self.graph.create(next_weibo)
                # self.graph.create(repost_relationship)
            # elif item['pid']!=str(0) and item['pid']!='' and Weibo.select(self.graph).where(id=item['id']).first() != None: #中间层微博






        if isinstance(item, UserItem):
            user = User()

            user.id = item['id']
            user.image = item['image']
            user.name = item['name']
            user.cover = item['cover']
            user.description = item['description']
            user.follows_count = item['follows_count']
            user.fans_count = item['fans_count']
            user.gender = item['gender']
            user.statuses_count = item['statuses_count']
            user.verified = item['verified']
            user.verified_reason = item['verified_reason']
            user.verified_type = item['verified_type']
            user.flag = item['flag']

            self.graph.push(user) #插入用户信息节点















