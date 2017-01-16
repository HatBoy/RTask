# coding=UTF-8

from flask import Flask, render_template, request, redirect
from config import *
from control import *
from sutils.queues import get_redis_client

app = Flask(__name__)

##############################################任务队列##############################################

@app.route('/', methods=['GET', 'POST'])
@app.route('/index/', methods=['GET', 'POST'])
@app.route('/queues/', methods=['GET', 'POST'])
def index():
    redis_errors = redis_check()
    if len(redis_errors) > 0:
        return render_template('rediserror.html', redis_errors=redis_errors)
    name = request.args.get('name', 'ids')
    task_name = TASK_NAME
    queueinfo = QueueInfo()
    taskid_counts = queueinfo.taskid_counts()
    taskfail_counts = queueinfo.taskfail_counts()
    if name == 'fails':
        taskfail_range = queueinfo.taskfail_range(0, 99)
        return render_template('fails.html', task_name=task_name, taskid_counts=taskid_counts,
                               taskfail_counts=taskfail_counts, taskfail_range=taskfail_range)
    else:
        taskid_range = queueinfo.taskid_range(-100, -1)
        if not taskid_range:
            taskid_range = list()
        taskid_range.reverse()
        return render_template('index.html', task_name=task_name, taskid_counts=taskid_counts,
                               taskfail_counts=taskfail_counts, taskid_range=taskid_range)


@app.route('/taskfirst/', methods=['GET', 'POST'])
def taskid_first():
    taskid = request.args.get('taskid', None)
    queueinfo = QueueInfo()
    queueinfo.taskid_first(taskid)
    return redirect('/index/')


@app.route('/tasklast/', methods=['GET', 'POST'])
def taskid_last():
    taskid = request.args.get('taskid', None)
    queueinfo = QueueInfo()
    queueinfo.taskid_last(taskid)
    return redirect('/index/')


@app.route('/taskdelete/', methods=['GET', 'POST'])
def taskid_delete():
    taskid = request.args.get('taskid', None)
    queueinfo = QueueInfo()
    queueinfo.task_delete(TASK_NAME + ':task_ids', taskid)
    return redirect('/index/')


@app.route('/faildelete/', methods=['GET', 'POST'])
def taskfail_delete():
    taskfail = request.args.get('taskfail', None)
    queueinfo = QueueInfo()
    queueinfo.task_delete(TASK_NAME + ':task_fails', eval(taskfail))
    return redirect('/index/?name=fails')


@app.route('/failrpush/', methods=['GET', 'POST'])
def taskfail_rpush():
    taskfail = request.args.get('taskfail', None)
    queueinfo = QueueInfo()
    queueinfo.taskfail_rpush(eval(taskfail))
    return redirect('/index/?name=fails')


@app.route('/failallrpush/', methods=['GET', 'POST'])
def taskfail_all_rpush():
    queueinfo = QueueInfo()
    queueinfo.taskfail_all_rpush()
    return redirect('/index/?name=fails')


@app.route('/emptyfail/', methods=['GET', 'POST'])
def empty_fail():
    queueinfo = QueueInfo()
    queueinfo.taskfail_empty()
    return redirect('/index/?name=fails')


@app.route('/emptytask/', methods=['GET', 'POST'])
def empty_task():
    queueinfo = QueueInfo()
    queueinfo.taskid_empty()
    return redirect('/index/')


@app.route('/addtask/', methods=['GET', 'POST'])
def add_task():
    queueinfo = QueueInfo()
    if request.method == 'POST':
        taskid = request.form['taskid']
        if taskid.strip():
            queueinfo.taskid_add(taskid.strip())
    return redirect('/index/')


##############################################工作节点##############################################

@app.route('/nodes/', methods=['GET', 'POST'])
def node_lists():
    redis_errors = redis_check()
    if len(redis_errors) > 0:
        return render_template('rediserror.html', redis_errors=redis_errors)
    nodeinfo = NodeInfo()
    node_list = nodeinfo.node_list()
    newnode_list = list()
    node_nums = len(node_list)
    run_nodes = 0
    stop_nodes = 0
    for node in node_list:
        macid = node['macid']
        task_lists = nodeinfo.node_tasks(macid)
        task_nums = len(task_lists)
        run_nums = 0
        stop_nums = 0
        if task_nums > 0:
            status_show = '运行'
            run_nodes += 1
        else:
            status_show = '停止'
            stop_nodes += 1
        for task in task_lists:
            status = task['status']
            if status == 'run':
                run_nums += 1
            else:
                stop_nums += 1
        node['status_show'] = status_show
        node['task_nums'] = task_nums
        node['run_nums'] = run_nums
        node['stop_nums'] = stop_nums
        newnode_list.append(node)
    return render_template('nodes.html', node_list=newnode_list, node_nums=node_nums, run_nodes=run_nodes,
                           stop_nodes=stop_nodes)


@app.route('/nodeinfo/', methods=['GET', 'POST'])
def node_info():
    rpcip = request.args.get('rpcip', None)
    if rpcip.strip():
        ip = rpcip.split(':')[1][2:]
        serverinfo = ServerInfo(ip)
        nodeinfo = NodeInfo()
        system_infos = serverinfo.get_sysinfo()
        cpu_info = system_infos['cpu_info']
        memory_info = system_infos['memory_info']
        disk_info = system_infos['disk_info']
        network_info = system_infos['network_info']
        macid = system_infos['macid']
        base_info = nodeinfo.node_search(macid)
        task_lists = nodeinfo.node_tasks(macid)
        base_info['task_nums'] = len(task_lists)
        newtask_lists = list()
        run_nums = 0
        stop_nums = 0
        for task in task_lists:
            status = task['status']
            if status == 'run':
                status_show = '运行'
                operation = '停止'
                run_nums += 1
            else:
                status_show = '停止'
                operation = '运行'
                stop_nums += 1
            task['status_show'] = status_show
            task['operation'] = operation
            newtask_lists.append(task)
    return render_template('nodeinfo.html', base_info=base_info, cpu_info=cpu_info, memory_info=memory_info,
                           disk_info=disk_info, network_info=network_info, task_lists=newtask_lists, run_nums=run_nums,
                           stop_nums=stop_nums)


@app.route('/nodestop/', methods=['GET', 'POST'])
def node_stop():
    rpcip = request.args.get('rpcip', None)
    if rpcip.strip():
        ip = rpcip.split(':')[1][2:]
        workercontrol = WorkerControl(ip)
        workercontrol.kill_worker()
    return redirect('/nodes/')


@app.route('/nodedelete/', methods=['GET', 'POST'])
def node_delete():
    rpcip = request.args.get('rpcip', None)
    if rpcip.strip():
        ip = rpcip.split(':')[1][2:]
        workercontrol = WorkerControl(ip)
        workercontrol.exit_rpc()
    return redirect('/nodes/')


##############################################运行进程##############################################

@app.route('/workers/', methods=['GET', 'POST'])
def worker_lists():
    redis_errors = redis_check()
    if len(redis_errors) > 0:
        return render_template('rediserror.html', redis_errors=redis_errors)
    nodeinfo = NodeInfo()
    task_lists = nodeinfo.task_list()
    node_lists = nodeinfo.node_list()
    newtask_lists = list()
    task_nums = len(task_lists)
    run_nums = 0
    stop_nums = 0
    for task in task_lists:
        status = task['status']
        if status == 'run':
            status_show = '运行'
            operation = '停止'
            run_nums += 1
        else:
            status_show = '停止'
            operation = '运行'
            stop_nums += 1
        task['status_show'] = status_show
        task['operation'] = operation
        newtask_lists.append(task)
    return render_template('workers.html', task_lists=newtask_lists, task_nums=task_nums, run_nums=run_nums,
                           stop_nums=stop_nums, node_lists=node_lists)


# 停止或者开始单个进程
@app.route('/worker_control/', methods=['GET', 'POST'])
def worker_control():
    status = request.args.get('status', None)
    rpcip = request.args.get('rpcip', None)
    task_uuid = request.args.get('task_uuid', None)
    page = request.args.get('page', None)
    if status and rpcip and task_uuid and page:
        ip = rpcip.split(':')[1][2:]
        workercontrol = WorkerControl(ip)
        if status == 'run':
            workercontrol.stop_task(task_uuid)
        else:
            workercontrol.restart_task(task_uuid)
        if page == 'workers':
            return redirect('/workers/')
        else:
            return redirect('/nodeinfo/?rpcip=' + rpcip)


@app.route('/startworkers/', methods=['GET', 'POST'])
def start_workers():
    if request.method == 'GET':
        rpcip = request.form['rpcip']
        task_nums = request.form['task_nums']
    if request.method == 'POST':
        rpcip = request.form['rpcip']
        task_nums = request.form['task_nums']
    if rpcip and task_nums:
        try:
            task_nums = int(task_nums)
            if task_nums > 0:
                ip = rpcip.split(':')[1][2:]
                workercontrol = WorkerControl(ip)
                workercontrol.start_worker(task_nums)
        except Exception as e:
            pass
    return redirect('/nodeinfo/?rpcip=' + rpcip)


# 打开指定节点的所有进程
@app.route('/startalltasks/', methods=['GET', 'POST'])
def start_alltasks():
    rpcip = request.args.get('rpcip', None)
    if rpcip.strip():
        ip = rpcip.split(':')[1][2:]
        workercontrol = WorkerControl(ip)
        workercontrol.restart_alltasks()
    return redirect('/nodeinfo/?rpcip=' + rpcip)


# 打开所有节点的所有进程
@app.route('/alltasksstart/', methods=['GET', 'POST'])
def alltasks_start():
    nodeinfo = NodeInfo()
    nodeinfo.start_alltasks()
    return redirect('/workers/')


# 关闭所有节点的所有进程
@app.route('/alltasksstop/', methods=['GET', 'POST'])
def alltasks_stop():
    nodeinfo = NodeInfo()
    nodeinfo.stop_alltasks()
    return redirect('/workers/')


# 关闭指定节点的所有进程
@app.route('/stopalltasks/', methods=['GET', 'POST'])
def stop_alltasks():
    rpcip = request.args.get('rpcip', None)
    if rpcip.strip():
        ip = rpcip.split(':')[1][2:]
        workercontrol = WorkerControl(ip)
        workercontrol.stop_alltasks()
    return redirect('/nodeinfo/?rpcip=' + rpcip)


##############################################Redis状态##############################################

def redis_check():
    redis_errors = list()
    try:
        queue_client = get_redis_client(QUEUE_REDIS_TYPE, QUEUE_REDIS_HOST, QUEUE_REDIS_PORT, QUEUE_REDIS_DB,
                                        QUEUE_REDIS_PWD, QUEUE_REDIS_NODES)
        queue_client.ping()
    except Exception as e:
        dest = 'Redis任务队列数据库连接失败!请检查Redis连接配置是否正确或者正常运行'
        redis_errors.append({'dest': dest, 'error': str(e)})
    if IS_FILTER:
        try:
            filter_client = get_redis_client(FILTER_REDIS_TYPE, FILTER_REDIS_HOST, FILTER_REDIS_PORT, FILTER_REDIS_DB,
                                             FILTER_REDIS_PWD, FILTER_REDIS_NODES)
            filter_client.ping()
        except Exception as e:
            dest = 'Redis数据去重数据库连接失败!请检查Redis连接配置是否正确或者正常运行'
            redis_errors.append({'dest': dest, 'error': str(e)})
    try:
        rtask_client = get_redis_client('single', RTASK_REDIS_HOST, RTASK_REDIS_POST, RTASK_REDIS_DB,
                                        RTASK_REDIS_PWD, None)
        rtask_client.ping()
    except Exception as e:
        dest = 'Redis RTask控制数据库连接失败!请检查Redis连接配置是否正确或者正常运行'
        redis_errors.append({'dest': dest, 'error': str(e)})
    return redis_errors


@app.route('/redis/', methods=['GET', 'POST'])
def redis_list():
    redis_errors = redis_check()
    if len(redis_errors) > 0:
        return render_template('rediserror.html', redis_errors=redis_errors)
    queue_client = get_redis_client(QUEUE_REDIS_TYPE, QUEUE_REDIS_HOST, QUEUE_REDIS_PORT, QUEUE_REDIS_DB,
                                    QUEUE_REDIS_PWD, QUEUE_REDIS_NODES)
    filter_client = get_redis_client(FILTER_REDIS_TYPE, FILTER_REDIS_HOST, FILTER_REDIS_PORT, FILTER_REDIS_DB,
                                     FILTER_REDIS_PWD, FILTER_REDIS_NODES)
    rtask_client = get_redis_client('single', RTASK_REDIS_HOST, RTASK_REDIS_POST, RTASK_REDIS_DB,
                                    RTASK_REDIS_PWD)
    redis_lists = list()

    redisinfo_queue = RedisInfo(queue_client)
    queue_info = redisinfo_queue.info()
    queue_dict = {'dest': 'Redis任务队列数据库', 'name': 'queue'}
    if QUEUE_REDIS_TYPE == 'single':
        queue_dict['type'] = '单机'
        queue_dict['ip_port'] = QUEUE_REDIS_HOST + ' : ' + str(QUEUE_REDIS_PORT)
        queue_dict['dbsize'] = queue_client.dbsize()
        queue_dict['clients'] = queue_info['connected_clients']
        queue_dict['used_memory'] = queue_info['used_memory_human']
    elif QUEUE_REDIS_TYPE == 'cluster':
        queue_dict['type'] = '集群'
        queue_dict['ip_port'] = [node['host'] + ' : ' + node['port'] for node in QUEUE_REDIS_NODES]
        queue_dict['dbsize'] = [k + ' : ' + str(v) for k, v in queue_client.dbsize().items()]
        queue_dict['clients'] = [k + ' : ' + str(v['connected_clients']) for k, v in queue_info.items()]
        queue_dict['used_memory'] = [k + ' : ' + v['used_memory_human'] for k, v in queue_info.items()]
    redis_lists.append(queue_dict)

    if IS_FILTER:
        redisinfo_filter = RedisInfo(filter_client)
        filter_info = redisinfo_filter.info()
        filter_dict = {'dest': 'Redis数据去重数据库', 'name': 'filter'}
        if FILTER_REDIS_TYPE == 'single':
            filter_dict['type'] = '单机'
            filter_dict['ip_port'] = FILTER_REDIS_HOST + ' : ' + str(FILTER_REDIS_PORT)
            filter_dict['dbsize'] = filter_client.dbsize()
            filter_dict['clients'] = filter_info['connected_clients']
            filter_dict['used_memory'] = filter_info['used_memory_human']
        elif FILTER_REDIS_TYPE == 'cluster':
            filter_dict['type'] = '集群'
            filter_dict['ip_port'] = [node['host'] + ' : ' + node['port'] for node in FILTER_REDIS_NODES]
            filter_dict['dbsize'] = [k + ' : ' + str(v) for k, v in filter_client.dbsize().items()]
            filter_dict['clients'] = [k + ' : ' + str(v['connected_clients']) for k, v in filter_info.items()]
            filter_dict['used_memory'] = [k + ' : ' + v['used_memory_human'] for k, v in filter_info.items()]
        redis_lists.append(filter_dict)

    redisinfo_rtask = RedisInfo(rtask_client)
    rtask_info = redisinfo_rtask.info()
    rtask_dict = {'dest': 'Redis RTask控制数据库', 'name': 'rtask'}
    rtask_dict['type'] = '单机'
    rtask_dict['ip_port'] = RTASK_REDIS_HOST + ' : ' + str(RTASK_REDIS_POST)
    rtask_dict['dbsize'] = rtask_client.dbsize()
    rtask_dict['clients'] = rtask_info['connected_clients']
    rtask_dict['used_memory'] = rtask_info['used_memory_human']
    redis_lists.append(rtask_dict)
    return render_template('redis.html', redis_lists=redis_lists)


@app.route('/redisinfo/', methods=['GET', 'POST'])
def redis_info():
    name = request.args.get('name', None)
    if name == 'queue':
        redis_client = get_redis_client(QUEUE_REDIS_TYPE, QUEUE_REDIS_HOST, QUEUE_REDIS_PORT, QUEUE_REDIS_DB,
                                        QUEUE_REDIS_PWD, QUEUE_REDIS_NODES)
        redis_type = QUEUE_REDIS_TYPE
    elif name == 'filter':
        redis_client = get_redis_client(FILTER_REDIS_TYPE, FILTER_REDIS_HOST, FILTER_REDIS_PORT, FILTER_REDIS_DB,
                                         FILTER_REDIS_PWD, FILTER_REDIS_NODES)
        redis_type = FILTER_REDIS_TYPE
    elif name == 'rtask':
        redis_client = get_redis_client('single', RTASK_REDIS_HOST, RTASK_REDIS_POST, RTASK_REDIS_DB,
                                        RTASK_REDIS_PWD)
        redis_type = 'single'
    else:
        return redirect('/redis/')

    redisinfo = RedisInfo(redis_client)
    redis_info = redisinfo.info()
    redis_config = redisinfo.config_get()
    redis_clients = redisinfo.client_list()
    return render_template('redisinfo.html', redis_info=redis_info, redis_config=redis_config,
                           redis_clients=redis_clients, redis_type=redis_type)

@app.route('/redissave/', methods=['GET', 'POST'])
def redis_save():
    name = request.args.get('name', None)
    save_type = request.args.get('save_type', None)
    if name == 'queue':
        if QUEUE_REDIS_TYPE == 'single':
            timeout = 3
        else:
            timeout = None
        redis_client = get_redis_client(QUEUE_REDIS_TYPE, QUEUE_REDIS_HOST, QUEUE_REDIS_PORT, QUEUE_REDIS_DB,
                                        QUEUE_REDIS_PWD, QUEUE_REDIS_NODES, timeout=timeout)
    elif name == 'filter':
        if FILTER_REDIS_TYPE == 'single':
            timeout = 3
        else:
            timeout = None
        redis_client = get_redis_client(FILTER_REDIS_TYPE, FILTER_REDIS_HOST, FILTER_REDIS_PORT, FILTER_REDIS_DB,
                                         FILTER_REDIS_PWD, FILTER_REDIS_NODES, timeout=timeout)
    elif name == 'rtask':
        redis_client = get_redis_client('single', RTASK_REDIS_HOST, RTASK_REDIS_POST, RTASK_REDIS_DB,
                                        RTASK_REDIS_PWD)
    else:
        return redirect('/redis/')
    redisinfo = RedisInfo(redis_client)
    if save_type == 'save':
        redisinfo.save(is_bgsave=False)
    else:
        redisinfo.save(is_bgsave=True)
    return redirect('/redis/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)