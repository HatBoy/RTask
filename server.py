#coding=UTF-8

import uuid
import redis
import time
import zerorpc
from sutils import sysinfo
from sutils import wcontrol
from worker import run_task
from config import *

class RPCServer():

    def __init__(self):
        self.pool = redis.ConnectionPool(host=RTASK_REDIS_HOST, port=RTASK_REDIS_POST, db=RTASK_REDIS_DB, password=RTASK_REDIS_PWD, encoding='utf-8', decode_responses=True)
        self.client = redis.StrictRedis(connection_pool=self.pool)
        self.macid = sysinfo.get_macid()
        self.ips = sysinfo.get_ips()
        self.hostname = sysinfo.get_hostname()
        self.platform = sysinfo.get_platform()

    def pwd_check(self, password):
        if RPC_PWD == password:
            return True
        else:
            return False

    def ping(self):
        return True

    def register_host(self, tasks=None):
        if tasks is None:
            tasks = list()
        host_data = {'macid':self.macid, 'tasks':tasks, 'ips':self.ips, 'hostname':self.hostname, 'platform':self.platform}
        self.client.hset(TASK_NAME+':task_nodes', self.macid, host_data)
        return True

    def unregister_host(self):
        self.client.hdel(TASK_NAME+':task_nodes', self.macid)
        return True

    def start_worker(self, worker_nums=10, password=None):
        if self.pwd_check(password):
            try:
                wc = wcontrol.WorkerCotrol()
                wc.kill_worker()
                self.unregister_tasks()
                wc.start_worker(worker_nums)
                self._start_task(worker_nums)
                return 'OK'
            except Exception as e:
                return 'ERROR : ' + str(e)
        else:
            return "Password Error!"

    def kill_worker(self, password):
        if self.pwd_check(password):
            try:
                wc = wcontrol.WorkerCotrol()
                wc.kill_worker()
                self.unregister_tasks()
                self.register_host()
                return 'OK'
            except Exception as e:
                return 'ERROR : ' + str(e)
        else:
            return "Password Error!"

    def worker_status(self, password):
        if self.pwd_check(password):
            wc = wcontrol.WorkerCotrol()
            status = wc.worker_status()
            return status
        else:
            return "Password Error!"

    def _start_task(self, task_nums=10):
        task_uuids = list()
        for i in range(task_nums):
            task_uuid = str(uuid.uuid4())
            run_task(task_uuid)
            task_uuids.append(task_uuid)
        self.register_host(task_uuids)
        self.register_tasks(task_uuids)

    def get_taskuuids(self):
        task_node = self.client.hget(TASK_NAME+':task_nodes', self.macid)
        task_uuids = eval(task_node)['tasks']
        return task_uuids

    def register_tasks(self, task_uuids):
        for task_uuid in task_uuids:
            data = {'macid':self.macid, 'status':'run', 'task_uuid':task_uuid, 'hostname':self.hostname}
            self.client.hset(TASK_NAME+':task_status', task_uuid, data)

    def unregister_tasks(self):
        task_uuids = self.get_taskuuids()
        for task_uuid in task_uuids:
            self.client.hdel(TASK_NAME+':task_status', task_uuid)

    def stop_task(self, task_uuid, password):
        if self.pwd_check(password):
            data = {'macid':self.macid, 'status':'stop', 'task_uuid':task_uuid, 'hostname':self.hostname}
            self.client.hset(TASK_NAME+':task_status', task_uuid, data)
            return True
        else:
            return "Password Error!"

    def restart_task(self, task_uuid, password):
        if self.pwd_check(password):
            data = {'macid':self.macid, 'status':'run', 'task_uuid':task_uuid, 'hostname':self.hostname}
            self.client.hset(TASK_NAME+':task_status', task_uuid, data)
            return True
        else:
            return "Password Error!"

    def stop_alltasks(self, password):
        if self.pwd_check(password):
            task_uuids = self.get_taskuuids()
            for task_uuid in task_uuids:
                self.stop_task(task_uuid, RPC_PWD)
            return True
        else:
            return "Password Error!"

    def restart_alltasks(self, password):
        if self.pwd_check(password):
            task_uuids = self.get_taskuuids()
            for task_uuid in task_uuids:
                self.restart_task(task_uuid, RPC_PWD)
            return True
        else:
            return "Password Error!"

    def sysinfo(self, password):
        if self.pwd_check(password):
            cpu_info = sysinfo.get_cpu()
            memory_info = sysinfo.get_memory()
            disk_info = sysinfo.get_disk()
            network_info = sysinfo.get_network()
            return {'macid':self.macid, 'cpu_info':cpu_info, 'memory_info':memory_info, 'disk_info':disk_info, 'network_info':network_info}
        else:
            return "Password Error!"

    def exit_rpc(self, password):
        if self.pwd_check(password):
            self.kill_worker(RPC_PWD)
            self.unregister_host()
            exit()
        else:
            return "Password Error!"

try:
    rpc = RPCServer()
    rpc.register_host()
    s = zerorpc.Server(RPCServer())
    s.bind("tcp://0.0.0.0:{rpc_port}".format(rpc_port=RPC_PORT))
    s.run()
except KeyboardInterrupt:
    rpc.kill_worker(RPC_PWD)
    rpc.unregister_host()
except Exception as e:
    datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open('./logs/worker.err', 'a', encoding='UTF-8') as f:
        f.write('ErrorTime : ' + datetime + '\n')
        f.write('ErrorData : ' + str(e) + '\n')
        f.write('##############################\n')