#coding=UTF-8

import random
import time

#任务执行主体，传入任务ID号，返回任务执行结果
def main(id):
    ids = list()
    for i in range(10):
        n = random.randint(0, 100000000)
        ids.append(str(n))
    time.sleep(3)
    return {'taskid':str(id), 'nextids':ids}


#保存任务执行结果
def save(data):
    pass