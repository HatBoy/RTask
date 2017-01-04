#coding=UTF-8

'''
使用Redis提供消息队列功能，存放任务队列和失败队列
'''

import redis
import rediscluster

class RedisQueues():

    def __init__(self, conn=None):
        self.redis = conn

    def push(self, key, value):
        return self.redis.lpush(key, value)

    def pop(self, key):
        raw = self.redis.rpop(key)
        if raw:
            data = raw
        else:
            data = None
        return data

    def index(self, key, i):
        raw = self.redis.lindex(key, i)
        if raw:
            data = raw
        else:
            data = None
        return data

    def range(self, key, start, end):
        raw = self.redis.lrange(key, start, end)
        if raw:
            data = raw
        else:
            data = None
        return data

    def first(self, key, value):
        self.delete_value(key, value)
        return self.redis.rpush(key, value)

    def last(self, key, value):
        self.delete_value(key, value)
        return self.redis.lpush(key, value)

    def len(self, key):
        return self.redis.llen(key)

    def delete_value(self, key, value):
        return self.redis.lrem(key, 0, value)

    def delete_key(self, key):
        return self.redis.delete(key)


#获取redis连接客户端
def get_redis_client(redis_type='single', host='127.0.0.1', port=6379, db=0, pwd=None, nodes=None, timeout=3):
    if redis_type == 'single':
        pool = redis.ConnectionPool(host=host, port=port, db=db, password=pwd, socket_timeout=timeout, socket_connect_timeout=timeout, encoding='utf-8', decode_responses=True)
        client = redis.StrictRedis(connection_pool=pool)
    else:
        client = rediscluster.StrictRedisCluster(startup_nodes=nodes, decode_responses=True, socket_timeout=timeout, socket_connect_timeout=timeout)
    return client

'''
import redis

pool = redis.ConnectionPool(host='192.168.100.6', port=6379, db=0)
client = redis.StrictRedis(connection_pool=pool)

rq = RedisQueues(client)

c = rq.pop(15)
print(rq.len())
'''