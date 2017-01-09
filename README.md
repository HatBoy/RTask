# RTask
## Python3+Huey+Zerorpc+Redis+Flask=RTask 轻量级分布式任务管理系统
### 系统简介:
只需要将任务执行脚本放在tasks目录或者其他目录，进行简单的配置，即可将任务变成分布式任务，并可通过web界面节点的任务进行监控和控制

### 运行原理:
将任务脚本放入tasks目录，脚本需要提供main函数并可传入一个参数供系统调用，用来传入任务id，如果需要将任务执行结果进行保存，将保存函数命名为save，并将需要存储的数据当做参数传入，系统将自动调用save函数存储运行结果；本系统利用redis数据库作为数据队列，数据去重数据库，节点监控数据库,配置文件config.py修改后，在节点机器运行python3 server.py即可，节点会自动在配置的redis数据库中注册节点的信息，监控端运行python3 monitor.py即可访问本地端口8888对节点和任务进行管理，管理端通过zerorpc远程调用控制节点，各个节点通过huey开启多个任务，每一个任务都是一个进程，注意任务数量不要太多，推荐使用协程写任务，然后开启适量的进程数量.

## 功能特点
+ 配置部署简单，只需要安装相应的第三方库，对配置文件进行简单的配置，运行server.py文件即可
+ 支持redis集群
+ 节点监控方便，可通过控制面板添加修改任务，启动指定数量任务，监控节点系统和redis系统状态
+ 内置数据去重算法，该系统最初为分布式爬虫而设计，故添加了两种数据去重算法，redis SET集合去重占用内存高，无错误率，适用于千万级别数据的去重，bloomfliter算法去重占用内存低，存在错误率，适用于上亿级别的数据去重

## 监控端展示
### 任务队列
![Alt Text](https://github.com/HatBoy/RTask/blob/master/images/queues.png)

### 节点展示
![Alt Text](https://github.com/HatBoy/RTask/blob/master/images/nodes.png)

### 节点状态展示
![Alt Text](https://github.com/HatBoy/RTask/blob/master/images/nodeinfo.png)

### 工作进程控制
![Alt Text](https://github.com/HatBoy/RTask/blob/master/images/workers.png)

### redis状态监控
![Alt Text](https://github.com/HatBoy/RTask/blob/master/images/redis.png)

## 系统使用配置
### 1.安装第三方依赖库和redis
### 2.编写任务脚本并预留main方法和save方法,save方法可选
### 3.配置任务
```Python3
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
```
### 4.在节点机器运行python3 server.py启动系统，在任意能访问节点和redis数据库的主机以相同的配置运行python3 monitor.py启动监控方
