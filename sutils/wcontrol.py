#coding=UTF-8

import subprocess
import os
import shlex

class WorkerCotrol():

    def start_worker(self, worker_name='worker', worker_nums=10):
        if os.path.exists('./logs/worker.log'):
            os.remove('./logs/worker.log')
        cmd = shlex.split('huey_consumer worker.huey -w {worker_nums} -k process -l ./logs/{worker_name}.log  -n'.format(worker_nums=worker_nums, worker_name=worker_name))
        self.sub = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return self.sub

    def kill_worker(self, worker_name='worker'):
        pids = os.popen('ps -aux|grep {worker_name}'.format(worker_name=worker_name)).readlines()
        pids = [pid.split()[1] for pid in pids if ('grep' not in pid)]
        if pids:
            pids_str = ' '.join(pids)
            kill = os.popen('kill -9 {pids_str}'.format(pids_str=pids_str))

    def worker_status(self):
        pids = os.popen('ps -aux|grep huey_consumer').readlines()
        workers = [pid.split()[1] for pid in pids if ('grep' not in pid) and ('defunct' not in pid)]
        zombies = [pid.split()[1] for pid in pids if ('defunct' in pid)]
        return {'workers':len(workers)-2, 'zombies':len(zombies)}