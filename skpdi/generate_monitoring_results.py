# -*- coding: utf-8 -*-

import random
import csv
import datetime

servers = [
'gudhskpdi-db-01',
'gudhskpdi-db-02',
'gudhskpdi-db-03',
'gudhskpdi-app-01',
'gudhskpdi-app-02',
'gudhskpdi-app-03',
'gudhskpdi-ceph-01',
'gudhskpdi-ceph-02',
'gudhskpdi-ceph-03',
'gudhskpdi-bal-01'
]
metrics = [
# Format [Metric name, random lower, random higher]
['idle time', 51, 100],
['user time', 0, 49],
['system time',  0, 49],
['iowait time', 0, 19],
['nice time', 0, 19],
['interrupt time', 0, 19],
['softirq time', 0, 19],
['steal time', 0, 19],
['Processor load 1 min per core', 0.1, 0.9],
['Processor load 5 min per core', 0.1, 1.9],
['Processor load 15 min per core', 0.1, 1.9],
['Available memory', 5001, 10000],
['Total swap space', 1, 49],
['Free swap space', 91, 100],
['Free disk space HDD1', 50, 51], 
['Free disk space HDD2', 50, 51],
['Read op/s', 1, 99],
['Write op/s', 1, 99],
['Read Mb/s', 1, 10],
['Write Mb/s' ,1, 10],
['Incoming traffic', 1, 10],
['Outgoing traffic', 1, 10]
]

servers_db = [
'gudhskpdi-db-01',
'gudhskpdi-db-02',
'gudhskpdi-db-03'
]

metrics_db = [
['PostgreSQL number of active connections', 1, 69],
['Database size', 1299, 1300],
['PostgreSQL service uptime',600 , 50000],
['PostgreSQL streaming replication lag', 1,149],
['PostgreSQL ping', 1, 9]
]

servers_app = [
'gudhskpdi-app-01',
'gudhskpdi-app-02',
'gudhskpdi-app-03'
]

metrics_app = [
['Веб запрос к службе', 1, 4]
]

servers_ceph = [
'gudhskpdi-ceph-01',
'gudhskpdi-ceph-02',
'gudhskpdi-ceph-03'
]

metrics_ceph = [
['ceph free space', 1000, 9999],
['ceph latency',1 , 49],
['ceph i/o', 1,99],
['ceph bandwith',1 ,9],
['Веб запрос к службе', 1, 4]
]


servers_bal = [
'gudhskpdi-bal-01'    
]

metrics_bal = [
['Веб запрос к службе', 1, 4]
]


# timeframe generator
dt = datetime.datetime(2018, 11, 1)
end = datetime.datetime(2018, 12, 30, 23, 59, 59)
step = datetime.timedelta(minutes=1)
timestamps = []
while dt < end:
    timestamps.append(dt.strftime('%Y-%m-%d %H:%M'))
    dt += step        

def generator(servers, metrics):
    for server in servers:
        with open('c:/tmp/1/'+server+'.csv', mode='ab') as metrics_file:
            metrics_writer = csv.writer(metrics_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for stamp in timestamps:
                for metric in metrics:
                    a = random.uniform(metric[1], metric[2])
                    # append to csv to be here.
                    metrics_writer.writerow([server, metric[0], stamp,  str(a), 'HOPMA'])

generator(servers, metrics)
generator(servers_db, metrics_db)
generator(servers_app, metrics_app)
generator(servers_ceph, metrics_ceph)
generator(servers_bal, metrics_bal)