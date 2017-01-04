#coding=UTF-8

#配置文件，配置系统需要的数据库等参数

#任务配置
TASK_NAME = 'spider'
#任务返回的结果字典中taskid的名称
TASK_ID = 'id'
#是否开启自动扩展功能，如执行一个任务之后会解析出更多的任务
IS_NEXT = True
#任务返回的结果字典中待爬取的taskid的名称,必须是序列
NEXT_IDS = 'nextids'
#任务的模块名和路径
TASK_MODULE = 'tasks.spider'
#redis队列数据库配置
#redis类型，单机redis(single)还是集群redis(cluster)
QUEUE_REDIS_TYPE = 'single'
QUEUE_REDIS_HOST = '192.168.1.100'
QUEUE_REDIS_PORT = 6379
QUEUE_REDIS_DB = 0
QUEUE_REDIS_PWD = '123456'
QUEUE_REDIS_NODES = [{"host": "127.0.0.1", "port": "7000"}, {"host": "127.0.0.1", "port": "7001"}, {"host": "127.0.0.1", "port": "7002"}, {"host": "127.0.0.1", "port": "7003"}]

#是否将任务返回的结果保存，如果保存，则自动调用任务的save方法将数据传入
IS_SAVE = True

#去重配置
#是否开启任务去重功能
IS_FILTER = True
#去重方式，redis集合(set)去重或者bloomfilter算法(bloom)去重
FILTER_TYPE = 'set'
FILTER_REDIS_TYPE = 'single'
FILTER_REDIS_HOST = '192.168.1.101'
FILTER_REDIS_PORT = 6379
FILTER_REDIS_DB = 0
FILTER_REDIS_PWD = '123456'
#redis集群节点
FILTER_REDIS_NODES = [{"host": "127.0.0.1", "port": "7000"}, {"host": "127.0.0.1", "port": "7001"}, {"host": "127.0.0.1", "port": "7002"}, {"host": "127.0.0.1", "port": "7003"}]
#若使用BloomFilter算法去重需要预先知道要去重的数量和错误率
CAPACITY = 100000000
ERROR_RATE = 0.00000001

#RTask配置,只能是单机redis不支持集群,于存放各个节点,worker等信息,无需集群
RTASK_REDIS_HOST = '192.168.1.102'
RTASK_REDIS_POST = 6379
RTASK_REDIS_DB = 0
#RTASK_REDIS_PWD = None
RTASK_REDIS_PWD = '123456'
#RPC远程连接端口
RPC_PORT = 5555
#远程RPC控制认证密码
RPC_PWD = '123456'