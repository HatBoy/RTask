# RTask
## Python3+Huey+Zreorpc+Redis+Flask=RTask 轻量级分布式任务管理系统
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
![Alt Text](https://github.com/HatBoy/RTask/tree/master/images/queues.png)

### 节点展示
![Alt Text](https://github.com/HatBoy/RTask/tree/master/images/nodes.png)

### 节点状态展示
![Alt Text](https://github.com/HatBoy/RTask/tree/master/images/nodeinfo.png)

### 工作进程控制
![Alt Text](https://github.com/HatBoy/RTask/tree/master/images/workers.png)

### redis状态监控
![Alt Text](https://github.com/HatBoy/RTask/tree/master/images/redis.png)