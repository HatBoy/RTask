#coding=UTF-8

import importlib
import time
import redis
from huey import RedisHuey
from config import *
from sutils import filter
from sutils import queues

task = importlib.import_module(TASK_MODULE)
pool = redis.ConnectionPool(host=RTASK_REDIS_HOST, port=RTASK_REDIS_POST, db=RTASK_REDIS_DB, password=RTASK_REDIS_PWD)
huey = RedisHuey(TASK_NAME, connection_pool=pool, result_store=False)


#获取去重对象
def get_filter(filter_type='set', redis_type='single', host='127.0.0.1', port=6379, db=0, pwd=None, nodes=None, capacity=100000000, error_rate=0.00000001, key='task_filter'):
    redis_client = queues.get_redis_client(redis_type, host, port, db, pwd, nodes)
    if filter_type == 'set':
        filter_client = filter.RedisFilter(conn=redis_client, key=key)
    elif filter_type == 'bloom':
        filter_client = filter.BloomFilter(conn=redis_client, capacity=capacity, error_rate=error_rate, key=key)
    return filter_client


queue_client = queues.get_redis_client(QUEUE_REDIS_TYPE, QUEUE_REDIS_HOST, QUEUE_REDIS_PORT, QUEUE_REDIS_DB, QUEUE_REDIS_PWD, QUEUE_REDIS_NODES)
task_queues = queues.RedisQueues(conn=queue_client)
if IS_FILTER:
    filter_client = get_filter(FILTER_TYPE, FILTER_REDIS_TYPE, FILTER_REDIS_HOST, FILTER_REDIS_PORT, FILTER_REDIS_DB, FILTER_REDIS_PWD,
                                   FILTER_REDIS_NODES, CAPACITY, ERROR_RATE, TASK_NAME+':filter')
control_pool = redis.ConnectionPool(host=RTASK_REDIS_HOST, port=RTASK_REDIS_POST, db=RTASK_REDIS_DB, password=RTASK_REDIS_PWD, encoding='utf-8', decode_responses=True)
control_client = redis.StrictRedis(connection_pool=control_pool)

ERROR_NUMS = 0

@huey.task()
def run_task(uuid):
    global ERROR_NUMS
    taskid = None
    while True:
        try:
            if ERROR_NUMS > MAX_ERROR_NUMS:
                ERROR_NUMS = 0
                time.sleep(ERROR_SLEEP)
            status_data = control_client.hget(TASK_NAME+':task_status', uuid)
            status = eval(status_data)['status']
            if status == 'stop':
                time.sleep(30)
                continue
            taskid = task_queues.pop(TASK_NAME+':task_ids')
            if not taskid:
                time.sleep(30)
                continue
            if IS_FILTER and filter_client.is_exist(taskid):
                continue
            data = task.main(taskid)
            if not data:
                continue
            if IS_SAVE:
                task.save(data)
            if IS_FILTER:
                filter_client.add(data[TASK_ID])
            if IS_NEXT:
                nextids = data[NEXT_IDS]
                for id in nextids:
                    if IS_FILTER:
                        if not filter_client.is_exist(id):
                            task_queues.push(TASK_NAME+':task_ids', id)
                    else:
                        task_queues.push(TASK_NAME+':task_ids', id)
            ERROR_NUMS = 0
        except Exception as e:
            ERROR_NUMS += 1
            fail_data = {'taskid':str(taskid), 'error':str(e)}
            task_queues.push(TASK_NAME+':task_fails', fail_data)

def run_task_test(uuid):
    taskid = None
    while True:
        taskid = task_queues.pop(TASK_NAME+':task_ids')
        if not taskid:
            time.sleep(30)
            continue
        if IS_FILTER and filter_client.is_exist(taskid):
            continue
        data = task.main(taskid)
        print(data.keys())
        if not data:
            continue
        if IS_SAVE:
            task.save(data)
        if IS_FILTER:
            filter_client.add(data[TASK_ID])
        if IS_NEXT:
            nextids = data[NEXT_IDS]
            print(nextids)
            for id in nextids:
                if IS_FILTER:
                    if not filter_client.is_exist(id):
                        task_queues.push(TASK_NAME+':task_ids', id)
                else:
                    task_queues.push(TASK_NAME+':task_ids', id)

#run_task_test('34229028')