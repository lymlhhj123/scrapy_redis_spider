#-*-coding:utf-8-*-
import redis
import pymysql
import sqlalchemy
from scrapy import signals
from twisted.enterprise import adbapi

class MySQL(object):
	#阻塞版本
	def __init__(self, name_or_url, **kwargs):
		"""
		create_engine是个函数
		"""
		self.db = sqlalchemy.create_engine(name_or_url, **kwargs)

	def _get_connection(self):
		conn = self.db.connect()
		return conn

	def select(self, cmd, item=()):
		"""
		对数据库不会造成状态改变的就用这条语句
		比如: select()
		"""
		cnx = self._get_connection()
		#下面返回的middle类似于游标
		#所以需要调用fetchall()才可以获得结果
		#调用close()就会把连接释放回连接池
		middle = cnx.execute(cmd, item)
		result = middle.fetchall()
		cnx.close()
		return result

	def query(self, cmd, item=()):
		"""
		对数据库会造成状态改变的就用这条语句
		比如: insert()
		注意这里是自动commit的
		"""
		cnx = self._get_connection()
		cnx.execute(cmd, item)		
		cnx.close()


class RedisPool(redis.StrictRedis):
	#阻塞版本
	def __init__(self, **kwargs):
		super(RedisConnectionPool, self).__init__(**kwargs)

	def new_brpop(self, keyname):
		return self.brpop(keyname, 0)[1]
		
	def new_blpop(self, keyname):
		return self.blpop(keyname, 0)[1]
		

#####################################################################
#用于需要进行mysql数据库异步非阻塞操作的基类
class BaseAsyncMySQL(object):

	def __init__(self, crawler, config):
		self.crawler = crawler
		self.config = config

	@classmethod
	def from_crawler(cls, crawler):
		instance = cls(crawler, crawler.settings.get('TWISTED_MYSQL_CONFIG'))
		crawler.signals.connect(instance.opened_spider, signal=signals.spider_opened)
		crawler.signals.connect(instance.closed_spider, signal=signals.spider_closed)
		return instance
		
	def opened_spider(self, spider):
		self.db = adbapi.ConnectionPool(**self.config)

	def closed_spider(self, spider):
		self.db.close()