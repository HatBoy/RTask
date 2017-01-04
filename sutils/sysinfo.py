#coding=UTF-8

import hashlib
import datetime
import psutil
import getpass
import platform

def get_macid():
    ifaces = psutil.net_if_addrs()
    macs = list()
    for iface, info in ifaces.items():
        if iface == 'lo':
            continue
        ipv4_mac = info[-1].address
        macs.append(ipv4_mac)
    macs.sort()
    mac_str = ':'.join(macs)
    hash_str = hashlib.md5(mac_str.encode('UTF-8')).hexdigest()
    return hash_str

def get_ips():
    ifaces = psutil.net_if_addrs()
    ips = list()
    for iface, info in ifaces.items():
        if iface == 'lo':
            continue
        ip = info[0].address
        ips.append(ip)
    return ips

def get_hostname():
    user = getpass.getuser()
    host = platform.uname().node
    hostname = user+'@'+host
    return hostname

def get_platform():
    return platform.platform()

def get_cpu():
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    loadavg = list()
    with open('/proc/loadavg', 'r') as f:
        lines = f.readlines()
    line = lines[0].split()
    loadavg.append(line[0])
    loadavg.append(line[1])
    loadavg.append(line[2])
    cpu_percent = [str(cpu)+'%' for cpu in cpu_percent]
    return {'cpu_percent':cpu_percent, 'boot_time':boot_time, 'loadavg':loadavg}

def get_memory():
    memory = dict()
    virtual = psutil.virtual_memory()
    swap = psutil.swap_memory()
    memory['virtual_total'] = '%.2fMB' % (virtual.total/1024/1024)
    memory['virtual_available'] = '%.2fMB' % (virtual.available/1024/1024)
    memory['virtual_percent'] = str(virtual.percent)+'%'
    memory['virtual_used'] = '%.2fMB' % (virtual.used/1024/1024)
    memory['virtual_free'] = '%.2fMB' % (virtual.free/1024/1024)
    memory['virtual_active'] = '%.2fMB' % (virtual.active/1024/1024)
    memory['virtual_inactive'] = '%.2fMB' % (virtual.inactive/1024/1024)
    memory['virtual_buffers'] = '%.2fMB' % (virtual.buffers/1024/1024)
    memory['virtual_cached'] = '%.2fMB' % (virtual.cached/1024/1024)
    memory['virtual_shared'] = '%.2fMB' % (virtual.shared/1024/1024)
    memory['swap_total'] = '%.2fMB' % (swap.total/1024/1024)
    memory['swap_used'] = '%.2fMB' % (swap.used/1024/1024)
    memory['swap_free'] = '%.2fMB' % (swap.free/1024/1024)
    memory['swap_percent'] = str(swap.percent)+'%'
    memory['swap_sin'] = '%.2fMB' % (swap.sin/1024/1024)
    memory['swap_sout'] = '%.2fMB' % (swap.sout/1024/1024)
    return memory

def get_disk():
    all_disk = psutil.disk_usage('/')
    disk = dict()
    disk['total'] = '%.2fGB' % (all_disk.total/1024/1024/1024)
    disk['used'] = '%.2fGB' % (all_disk.used/1024/1024/1024)
    disk['free'] = '%.2fGB' % (all_disk.free/1024/1024/1024)
    disk['percent'] = str(all_disk.percent)+'%'
    return disk

def get_network():
    network = psutil.net_io_counters(pernic=True)
    ifaces = psutil.net_if_addrs()
    networks = list()
    for k, v in ifaces.items():
        ip = v[0].address
        data = network[k]
        ifnet = dict()
        ifnet['ip'] = ip
        ifnet['iface'] = k
        ifnet['sent'] = '%.2fMB' % (data.bytes_sent/1024/1024)
        ifnet['recv'] = '%.2fMB' % (data.bytes_recv/1024/1024)
        ifnet['packets_sent'] = data.packets_sent
        ifnet['packets_recv'] = data.packets_recv
        ifnet['errin'] = data.errin
        ifnet['errout'] = data.errout
        ifnet['dropin'] = data.dropin
        ifnet['dropout'] = data.dropout
        networks.append(ifnet)
    return networks