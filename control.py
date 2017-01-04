#coding=UTF-8

import redis
import zerorpc
from config import *
from sutils import queues


#节点信息
class NodeInfo():
    def __init__(self):
        self.pool = redis.ConnectionPool(host=RTASK_REDIS_HOST, port=RTASK_REDIS_POST, db=RTASK_REDIS_DB, password=RTASK_REDIS_PWD, encoding='utf-8', decode_responses=True)
        self.client = redis.StrictRedis(connection_pool=self.pool)

    def node_list(self):
        nodes = self.client.hgetall(TASK_NAME+':task_nodes')
        node_lists = list()
        for k, v in nodes.items():
            #macid = k.decode('UTF-8')
            data = eval(v)
            rpcip = None
            ips = data['ips']
            for ip in ips:
                if self.rpcconn_check(ip):
                    rpcip = ip
                    break
            data['rpcip'] = "tcp://{ip}:{port}".format(ip=rpcip, port=RPC_PORT)
            node_lists.append(data)
        return node_lists

    def node_search(self, macid):
        node = self.client.hget(TASK_NAME+':task_nodes', macid)
        node = eval(node)
        rpcip = None
        ips = node['ips']
        for ip in ips:
            if self.rpcconn_check(ip):
                rpcip = ip
                break
        node['rpcip'] = "tcp://{ip}:{port}".format(ip=rpcip, port=RPC_PORT)
        return node

    def rpcconn_check(self, ip):
        try:
            rpc = zerorpc.Client(timeout=3, heartbeat=3)
            rpc.connect("tcp://{ip}:{port}".format(ip=ip, port=RPC_PORT))
            ping = rpc.ping()
            rpc.close()
            return ping
        except Exception as e:
            return False

    def task_list(self):
        tasks = self.client.hgetall(TASK_NAME+':task_status')
        node_lists = self.node_list()
        macid_rpcip = dict()
        for node in node_lists:
            macid_rpcip[node['macid']] = node['rpcip']
        task_lists = list()
        for k, v in tasks.items():
            data = eval(v)
            data['rpcip'] = macid_rpcip[data['macid']]
            task_lists.append(data)
        task_lists.sort(key=lambda x:x['macid'])
        return task_lists

    def node_tasks(self, macid):
        nodes = self.client.hget(TASK_NAME+':task_nodes', macid)
        node_dict = eval(nodes)
        tasks = node_dict['tasks']
        task_lists = list()
        for t in tasks:
            task = self.client.hget(TASK_NAME+':task_status', t)
            task = eval(task)
            task_lists.append(task)
        return task_lists

    def start_alltasks(self):
        alltasks = self.client.hgetall(TASK_NAME+':task_status')
        for task_uuid, task_data in alltasks.items():
            task_uuid = task_uuid
            task_data = eval(task_data)
            status = task_data['status']
            if status == 'stop':
                task_data['status'] = 'run'
                self.client.hset(TASK_NAME+':task_status', task_uuid, task_data)

    def stop_alltasks(self):
        alltasks = self.client.hgetall(TASK_NAME + ':task_status')
        for task_uuid, task_data in alltasks.items():
            task_uuid = task_uuid
            task_data = eval(task_data)
            status = task_data['status']
            if status == 'run':
                task_data['status'] = 'stop'
                self.client.hset(TASK_NAME + ':task_status', task_uuid, task_data)

    def clear_data(self):
        self.client.delete(TASK_NAME+':task_nodes')
        self.client.delete(TASK_NAME+':task_status')

#服务端worker控制
class WorkerControl():

    def __init__(self, ip):
        self.rpc = zerorpc.Client(timeout=3, heartbeat=3)
        self.rpc.connect("tcp://{ip}:{port}".format(ip=ip, port=RPC_PORT))

    def ping(self):
        try:
            return self.rpc.ping()
        except Exception as e:
            return False

    def start_worker(self, worker_nums=10):
        result = self.rpc.start_worker(worker_nums, RPC_PWD)
        return result

    def kill_worker(self):
        result = self.rpc.kill_worker(RPC_PWD)
        return result

    def worker_status(self):
        status = self.rpc.worker_status(RPC_PWD)
        return status

    def stop_task(self, task_uuid):
        result = self.rpc.stop_task(task_uuid, RPC_PWD)
        return result

    def restart_task(self, task_uuid):
        result = self.rpc.restart_task(task_uuid, RPC_PWD)
        return result

    def stop_alltasks(self):
        result = self.rpc.stop_alltasks(RPC_PWD)
        return result

    def restart_alltasks(self):
        result = self.rpc.restart_alltasks(RPC_PWD)
        return result

    def exit_rpc(self):
        try:
            self.rpc.exit_rpc(RPC_PWD)
            return self.rpc.ping()
        except Exception as e:
            return True

    def close(self):
        self.rpc.close()

#任务队列信息
class QueueInfo():

    def __init__(self):
        self.client = queues.get_redis_client(QUEUE_REDIS_TYPE, QUEUE_REDIS_HOST, QUEUE_REDIS_PORT, QUEUE_REDIS_DB, QUEUE_REDIS_PWD, QUEUE_REDIS_NODES)
        self.queues = queues.RedisQueues(conn=self.client)

    def taskid_counts(self):
        return self.queues.len(TASK_NAME+':task_ids')

    def taskfail_counts(self):
        return self.queues.len(TASK_NAME+':task_fails')

    def taskid_range(self, start, end):
        return self.queues.range(TASK_NAME+':task_ids', start, end)

    def taskfail_range(self, start, end):
        fail_datas = self.queues.range(TASK_NAME+':task_fails', start, end)
        if fail_datas:
            return [eval(fail) for fail in fail_datas]
        else:
            return list()

    def task_index(self, key, index):
        return self.queues.index(key, index)

    def taskid_add(self, task_id):
        return self.queues.push(TASK_NAME+':task_ids', task_id)

    def task_delete(self, key, value):
        count = self.queues.delete_value(key, value)
        return count

    def taskid_first(self, task_id):
        return self.queues.first(TASK_NAME+':task_ids', task_id)

    def taskid_last(self, task_id):
        return self.queues.last(TASK_NAME+':task_ids', task_id)

    def taskfail_rpush(self, value):
        taskid = value['taskid']
        self.task_delete(TASK_NAME+':task_fails', value)
        return self.queues.push(TASK_NAME+':task_ids', taskid)

    def taskfail_all_rpush(self):
        fail_counts = self.taskfail_counts()
        fails = self.taskfail_range(0, fail_counts)
        fail_ids = [fail['taskid'] for fail in fails]
        self.queues.delete_key(TASK_NAME+':task_fails')
        for task_id in fail_ids:
            self.queues.push(TASK_NAME+':task_ids', task_id)
        return 'OK'

    def taskid_empty(self):
        return self.queues.delete_key(TASK_NAME+':task_ids')

    def taskfail_empty(self):
        return self.queues.delete_key(TASK_NAME+':task_fails')


#Redis信息
class RedisInfo():

    def __init__(self, conn=None):
        self.redis = conn

    def info(self):
        return self.redis.info()

    def config_get(self):
        return self.redis.config_get('*')

    def client_list(self):
        clients = self.redis.client_list()
        if isinstance(clients, list):
            client_lists = list()
            for client in clients:
                temps = list()
                for k, v in client.items():
                    temps.append(k+'='+v)
                client_lists.append(' '.join(temps))
            return client_lists
        else:
            client_dicts = dict()
            for ip, clients in clients.items():
                client_lists = list()
                for client in clients:
                    temps = list()
                    for k, v in client.items():
                        temps.append(k + '=' + v)
                    client_lists.append(' '.join(temps))
                client_dicts[ip] = client_lists
            return client_dicts
        
    def save(self, is_bgsave=False):
        if is_bgsave:
            return self.redis.bgsave()
        else:
            return self.redis.save()


#节点服务器系统信息
class ServerInfo():

    def __init__(self, ip):
        self.rpc = zerorpc.Client(timeout=3, heartbeat=3)
        self.rpc.connect("tcp://{ip}:{port}".format(ip=ip, port=RPC_PORT))

    def get_sysinfo(self):
        sysinfo = self.rpc.sysinfo(RPC_PWD)
        return sysinfo

# client = queues.get_redis_client(QUEUE_REDIS_TYPE, QUEUE_REDIS_HOST, QUEUE_REDIS_PORT, QUEUE_REDIS_DB, QUEUE_REDIS_PWD, QUEUE_REDIS_NODES)
# queues = queues.RedisQueues(conn=client)


# pool = redis.ConnectionPool(host=QUEUE_REDIS_HOST, port=QUEUE_REDIS_PORT, db=QUEUE_REDIS_DB, password=QUEUE_REDIS_PWD)
# client = redis.StrictRedis(connection_pool=pool)

# qi = QueueInfo()
# qi.taskfail_rpush({'taskid': '27050696', 'error': "module 'tasks.spider' has no attribute 'save'"})

# ni = NodeInfo()
# ni.task_list()