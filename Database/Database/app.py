from flask import Flask, jsonify,request, Response
from flask_cors import CORS 
from flask_sqlalchemy import SQLAlchemy
import string
import csv
import pandas as pd
import json
import datetime
import pytz
from pytz import timezone
import requests
import ast
import math

from multiprocessing import Process, Value, Lock
#Install psycopg2-binary
#Install waitress
#sudo pip3 install apscheduler==2.1.2

import pika
import uuid
import pickle

import time
import atexit
from apscheduler.scheduler import Scheduler

import docker

import os
import sys

import kazoo
from kazoo.client import KazooClient
from kazoo.client import KazooState

######################################################

def my_zookeeper_listener(state):  #KEEPS WATCH ON ZOOKEEPER STATE
    if state == KazooState.LOST:
        print("\n\tSESSION LOST\n")
    elif state == KazooState.SUSPENDED:
        print("\n\tSESSION SUSPENDED\n")
    else:
        print("\n\tSESSION CONNECTED / RECONNECTED\n")

zk = KazooClient(hosts='127.0.0.1:2181')
zk.add_listener(my_zookeeper_listener)

zk.start()

slave_path = "/slave"
master_path = "/master"

######################################################

if zk.exists(master_path):
    print("master path does exist. Deleting and Creating path")
    zk.delete(master_path, recursive=True)
    zk.create(master_path, ephemeral=False)
else:
    print("master path does NOT exist. Creating path")
    zk.create(master_path, ephemeral=False)

if zk.exists(slave_path):
    print("slave path does exist. Deleting and Creating path")
    zk.delete(slave_path, recursive=True)
    zk.create(slave_path, ephemeral=False)
else:
    print("slave path does NOT exist. Creating path")
    zk.create(slave_path, ephemeral=False)

######################################################

client = docker.from_env()

#########################################################

global slave_name_counter
slave_name_counter = 0
number_slaves_to_spawn = 1

for i in range(number_slaves_to_spawn):
    #
    container_name = str("ws_"+str(i))
    #client.containers.run("debian:stretch-slim", name=container_name, detach=True, tty=True)
    client.containers.run("worker:v1", name=container_name, detach=True)
    client.containers.get(container_name).exec_run("python3 Cloud-Computing-Course/Database/Database/rpc_server_database.py 1", detach =True)
    #client.containers.get(container_name).exec_run("ls", detach =True)
    print("STARTED Slave container\t", container_name)

    slave_name_counter += 1


#Adds slave and master to znodes
running_containers = client.containers.list()
slave_container_id_name_pid=[]
#master_container_id_name_pid=[]
for i in running_containers:
    if str(i.name).startswith("ws"):
        container_id = i.id
        container_name = i.name
        stream = os.popen("sudo docker inspect --format '{{ .State.Pid }}' " +'"' + str(container_id) + '"' )
        #DOCKER IP ADDRESS sudo sudo docker inspect -f '{{.NetworkSettings.IPAddress }}' wm01
        container_pid = stream.read()
        container_pid = int(container_pid)
        slave_container_id_name_pid.append( [str(container_id),str(container_name),str(container_pid)] )

        zk.create(slave_path + "/" + str(container_name))
        slave_container_id_name_pid_string = str(container_id)+" "+str(container_name)+" "+str(container_pid)
        zk.set(slave_path + "/" + str(container_name), slave_container_id_name_pid_string.encode('utf-8'))


zk.set(master_path, b"")

print("Initial slave_container_id_name_pid\t",slave_container_id_name_pid)

###############################################

@zk.ChildrenWatch(slave_path)
def watch_slave_node(children):
    print("\nSlave node change !! Current children:\t", children)

#@zk.DataWatch(master_path)
def watch_master_node(CHANGED):
    global slave_name_counter
    print("\nMaster Node data Change !! ")
    print("Leader Election !!")
    slave_list = zk.get_children(slave_path)
    slave_container_id_name_pid=[]
    for slave in slave_list:
        data, stat = zk.get(slave_path + "/" + slave)
        data = str( data.decode("utf-8") ).split(" ")
        slave_container_id_name_pid.append(data)
    
    if( len(slave_container_id_name_pid) == 0): ######
        print("ELECTION CANCEL !! No Slaves to pick from")
    
    else:
        min_container_id = int(sys.maxsize)
        min_container_name = int(sys.maxsize)
        min_container_pid = int(sys.maxsize)

        for i in slave_container_id_name_pid:
            if int( i[2] ) < int( min_container_pid ):
                min_container_id = i[0]
                min_container_name = i[1]
                min_container_pid = i[2]

        #KILL OLD PROCESSS AND START NEW MASTER PROCESS IN PYTHON
        
        client.containers.get(min_container_name).exec_run("pkill python", detach =True)
        client.containers.get(min_container_name).exec_run("python3 Cloud-Computing-Course/Database/Database/rpc_server_database.py 0", detach =True)
        #####

        zk.delete(slave_path + "/" + min_container_name, recursive=True)
        master_container_id_name_pid_string = str(min_container_id)+" "+str(min_container_name)+" "+str(min_container_pid)
        zk.set(master_path, master_container_id_name_pid_string.encode('utf-8'))
        print("NEW LEADER !! ", zk.get(master_path)[0].decode("utf-8")) 


        #####Start new slave to replace master
        container_name = str("ws_"+str(slave_name_counter))
        slave_name_counter += 1
        #client.containers.run("debian:stretch-slim", name=container_name, detach=True, tty=True)
        client.containers.run("worker:v1", name=container_name, detach=True)
        client.containers.get(container_name).exec_run("python3 Cloud-Computing-Course/Database/Database/rpc_server_database.py 1", detach =True)
        client.containers.get(container_name).exec_run("ls", detach =True)

        container_id = client.containers.get(container_name).id
        container_name = client.containers.get(container_name).name
        stream = os.popen("sudo docker inspect --format '{{ .State.Pid }}' " +'"' + str(container_id) + '"' )
        container_pid = stream.read()
        container_pid = int(container_pid)
        slave_container_id_name_pid.append( [str(container_id),str(container_name),str(container_pid)] )

        zk.create(slave_path + "/" + str(container_name))
        slave_container_id_name_pid_string = str(container_id)+" "+str(container_name)+" "+str(container_pid)
        zk.set(slave_path + "/" + str(container_name), slave_container_id_name_pid_string.encode('utf-8'))



time.sleep(1)
current_master = zk.get(master_path)[0].decode("utf-8")
print("current master is:\t", current_master)
time.sleep(1)

zk.exists(master_path, watch = watch_master_node)
zk.set(master_path, b"")

time.sleep(1)

#################################################

def incrementCount(val, lock):
    with lock:
        val.value += 1
def resetCount(val,lock):
    with lock:
        val.value = 0

v = Value('i', 0)  # v variable counts number of read requests
lock = Lock()
global previous_v
previous_v=0


########################################################

cron = Scheduler(daemon=True)


@cron.interval_schedule(seconds=30)
def job_function():
    global slave_name_counter
    global previous_v
    time_period_read_count = v.value - previous_v
    print("READ count value last x minutes is ", time_period_read_count)

    ################################   
    
    if time_period_read_count == 0:
        number_slaves_needed = 1
        
    else:
        number_slaves_needed = math.ceil( time_period_read_count/20 )
    print("Number of slaves needed = ", number_slaves_needed)
    

    number_slaves_running = len(zk.get_children(slave_path))
    #number_slaves_needed = time_period_read_count
    number_slaves_to_spawn = number_slaves_needed - number_slaves_running

    if number_slaves_to_spawn == 0:
        print("No Scale up or down.")
        
    elif number_slaves_to_spawn > 0:
        for i in range(number_slaves_to_spawn):
            time.sleep(0.25)
            container_name = str("ws_"+str(slave_name_counter))
            #client.containers.run("debian:stretch-slim", name=container_name, detach=True, tty=True)
            client.containers.run("worker:v1", name=container_name, detach=True)
            #client.containers.get(container_name).exec_run("ls", detach =True)
            client.containers.get(container_name).exec_run("python3 Cloud-Computing-Course/Database/Database/rpc_server_database.py 1", detach =True)
            print("STARTED Slave container\t", container_name)
            slave_name_counter += 1

            container_id = client.containers.get(container_name).id
            container_name = client.containers.get(container_name).name
            stream = os.popen("sudo docker inspect --format '{{ .State.Pid }}' " +'"' + str(container_id) + '"' )
            #DOCKER IP ADDRESS sudo sudo docker inspect -f '{{.NetworkSettings.IPAddress }}' wm01
            container_pid = stream.read()
            container_pid = int(container_pid)

            zk.create(slave_path + "/" + str(container_name))
            slave_container_id_name_pid_string = str(container_id)+" "+str(container_name)+" "+str(container_pid)
            zk.set(slave_path + "/" + str(container_name), slave_container_id_name_pid_string.encode('utf-8'))

        print("Finished Scale Up")

    else:
        for i in range( number_slaves_to_spawn * -1 ):
            time.sleep(0.25)
            slave_list = zk.get_children(slave_path)
            slave_container_id_name_pid=[]
            for slave in slave_list:
                data, stat = zk.get(slave_path + "/" + slave)
                data = str( data.decode("utf-8") ).split(" ")
                slave_container_id_name_pid.append(data)
            
            if( len(slave_container_id_name_pid) == 1):
                print("Scale Down Cancel !! No Slaves to pick from")
                break
            
            else:
                max_container_id = -1
                max_container_name = -1
                max_container_pid = -1

                for i in slave_container_id_name_pid:
                    if int( i[2] ) > int( max_container_pid ):
                        max_container_id = i[0]
                        max_container_name = i[1]
                        max_container_pid = i[2]

                client.containers.get(max_container_name).stop()
                client.containers.get(max_container_name).remove()
                zk.delete(slave_path + "/" + max_container_name, recursive=True)
                print("Deleted container\t",max_container_name)


    print(zk.get_children(slave_path))
    ################################

    previous_v= v.value


#######################################################


def at_exit_function():

    cron.shutdown(wait=False)

    running_containers = client.containers.list()
    for i in running_containers:
        if str(i.name).startswith("w"):
            i.stop()
            i.remove()
    print("Removed all master and slaves containers")

    zk.stop()



atexit.register(at_exit_function)
#atexit.register(lambda: cron.shutdown(wait=False))


###########################################################

app=Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Iusepostgres@321@52.73.30.120/Cloud_Computing_Assignment'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Iusepostgres@321@localhost/Cloud_Computing_Assignment'
db=SQLAlchemy(app)
CORS(app)
app.debug = True
#print('Connected to DB !!')
print("Ready !!")


##########################################################


class Area(db.Model):

    id=db.Column(db.Integer, primary_key=True)
    AreaNo=db.Column(db.Integer)
    AreaName=db.Column(db.String)

    def __init__(self,AreaNo,AreaName):
        self.AreaNo=AreaNo
        self.AreaName=AreaName
    
    def representation(self):
        return list([self.id,self.AreaNo,self.AreaName])


class User(db.Model):

    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String)
    password=db.Column(db.String)

    def __init__(self,username,password):
        self.username=username
        self.password=password

    def representation(self):
        print(list([self.id,self.username,self.password]))
        return(list([self.id,self.username,self.password]))

class Ride(db.Model):

    RideID=db.Column(db.Integer, primary_key=True)
    CreatedBy=db.Column(db.String)
    Users=db.Column(db.String)
    Timestamp=db.Column(db.DateTime)
    Source=db.Column(db.Integer)
    Destination=db.Column(db.Integer)

    def __init__(self, CreatedBy,Timestamp,Source,Destination):
        self.CreatedBy=CreatedBy
        self.Users=""
        self.Timestamp=Timestamp
        self.Source= Source
        self.Destination=Destination

    def representation(self):
        return(list([self.RideID,self.CreatedBy,self.Users,self.Timestamp,self.Source,self.Destination]))

try:
    Area.__table__.create(db.session.bind)
    with open('AreaNameEnum.csv', 'r') as file:
        data_df = pd.read_csv('AreaNameEnum.csv')
        for index,row in data_df.iterrows():
            new_area = Area(row['Area No'],row['Area Name'])
            db.session.add(new_area)
    db.session.commit()
except:
    pass


try:
    User.__table__.create(db.session.bind)
except:
    pass


try:
    Ride.__table__.create(db.session.bind)
except:
    pass

#################################################################
#"""

class FibonacciRpcClient_master(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='52.73.30.120', heartbeat=0))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue_master',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=n) ###
        while self.response is None:
            self.connection.process_data_events()
        return self.response

class FibonacciRpcClient_slave(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='52.73.30.120', heartbeat=0))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue_slave',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=str(n))
        while self.response is None:
            self.connection.process_data_events()
        return self.response

class FibonacciRpcClient_sync(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='52.73.30.120', heartbeat=0))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue_sync',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=n) ###
        while self.response is None:
            self.connection.process_data_events()
        return self.response



fibonacci_rpc_master = FibonacciRpcClient_master()
fibonacci_rpc_slave = FibonacciRpcClient_slave()
fibonacci_rpc_sync = FibonacciRpcClient_sync()

#"""

###############################################################
"""

print(" [x] Requesting Master fib('master')")
response = fibonacci_rpc_master.call('master')
print(" [.] Got %r" % response)
print(" [x] Requesting Sync fib('sync')")
response = fibonacci_rpc_sync.call('sync')
print(" [.] Got %r" % response)

print(" [x] Requesting Slave fib('slave')")
response = fibonacci_rpc_slave.call('slave')
print(" [.] Got %r" % response)

print(" [x] Requesting Master fib('master')")
response = fibonacci_rpc_master.call('master')
print(" [.] Got %r" % response)
print(" [x] Requesting Sync fib('sync')")
response = fibonacci_rpc_sync.call('sync')
print(" [.] Got %r" % response)

print(" [x] Requesting Slave fib('slave')")
response = fibonacci_rpc_slave.call('slave')
print(" [.] Got %r" % response)


"""
#####################################################################

    

@app.route('/api/v1/db/read',methods=['POST'])
def dbRead():

    if(v.value==0):
        # Explicitly kick off the background thread
        cron.start()
    incrementCount(v,lock)

    table=request.json['table']
    columns=request.json['columns']
    where=request.json['where']

    if(table=="user"):
        table_result = fibonacci_rpc_slave.call("read$user")
        table_result_deserialized = pickle.loads(table_result)
        print('table_result_deserialized ',table_result_deserialized)
        table_result_list=[]
        for i in table_result_deserialized:
            table_result_list.append(i.representation())

    elif(table=="ride"):
        table_result = fibonacci_rpc_slave.call("read$ride")
        table_result_deserialized = pickle.loads(table_result)
        print('table_result_deserialized ',table_result_deserialized)
        table_result_list=[]
        for i in table_result_deserialized:
            table_result_list.append(i.representation())

    elif(table=="area"):
        table_result = fibonacci_rpc_slave.call("read$area")
        table_result_deserialized = pickle.loads(table_result)
        print('table_result_deserialized ',table_result_deserialized)
        table_result_list=[]
        for i in table_result_deserialized:
            table_result_list.append(i.representation())

    else:
        table_result_list=[]
    print(table_result_list)
    return Response(json.dumps(table_result_list,default=str),status=200)


@app.route('/api/v1/db/write',methods=["POST"])
def dbWrite():
    #try:
        table=request.json['table']

        if(table=="user"):
            if 'insert' in request.json:
                insert=request.json['insert']
                insert_list=insert.split(";")
                username=str(insert_list[0])
                password=str(insert_list[1])

                new_user = User(username,password)

                message_sent = list( ["write" , "user", "insert" , new_user] )
                print('message_sent  ',message_sent)

                message_sent_serialized = pickle.dumps(message_sent)
                print('message_sent_serialized  ',message_sent_serialized)
                
                table_result = fibonacci_rpc_master.call(message_sent_serialized)
                table_result = fibonacci_rpc_sync.call(message_sent_serialized)

                print(table_result)
            
            if 'delete' in request.json:
                delete=request.json['delete']
                username=str(delete)

                message_sent = list( ["write" , "user", "delete" , username] )
                print('message_sent  ',message_sent)

                message_sent_serialized = pickle.dumps(message_sent)
                print('message_sent_serialized  ',message_sent_serialized)
                
                table_result = fibonacci_rpc_master.call(message_sent_serialized)
                table_result = fibonacci_rpc_sync.call(message_sent_serialized)
                print(table_result)



            if 'clear' in request.json:

                message_sent = list( ["write" , "user", "clear"] )
                print('message_sent  ',message_sent)

                message_sent_serialized = pickle.dumps(message_sent)
                print('message_sent_serialized  ',message_sent_serialized)
                
                table_result = fibonacci_rpc_master.call(message_sent_serialized)
                table_result = fibonacci_rpc_sync.call(message_sent_serialized)
                print(table_result)


        if(table=="ride"):
            if 'insert' in request.json:
                insert=request.json['insert']  
                print('Adding to ride table')
                insert_list=insert.split(";")
                CreatedBy=str(insert_list[0])
                Timestamp=str(insert_list[1])
                Source=int(insert_list[2])
                Destination=int(insert_list[3])
                TimestampObject= datetime.datetime.strptime(Timestamp,'%d-%m-%Y:%S-%M-%H')
                new_ride = Ride(CreatedBy,TimestampObject,Source,Destination)

                message_sent = list( ["write" , "ride", "insert" , new_ride] )
                print('message_sent  ',message_sent)

                message_sent_serialized = pickle.dumps(message_sent)
                print('message_sent_serialized  ',message_sent_serialized)
                
                table_result = fibonacci_rpc_master.call(message_sent_serialized)
                table_result = fibonacci_rpc_sync.call(message_sent_serialized)
                print(table_result)                


            
            if 'update' in request.json:
                update_list=request.json['update'].split(";")
                RideID=int(update_list[0])
                Username=str(update_list[1])

                message_sent = list( ["write" , "ride", "update" , RideID, Username] )
                print('message_sent  ',message_sent)

                message_sent_serialized = pickle.dumps(message_sent)
                print('message_sent_serialized  ',message_sent_serialized)
                
                table_result = fibonacci_rpc_master.call(message_sent_serialized)
                table_result = fibonacci_rpc_sync.call(message_sent_serialized)
                print(table_result) 



            if 'delete' in request.json:
                delete=request.json['delete']
                RideID=int(delete)

                message_sent = list( ["write" , "ride", "delete" , RideID] )
                print('message_sent  ',message_sent)

                message_sent_serialized = pickle.dumps(message_sent)
                print('message_sent_serialized  ',message_sent_serialized)
                
                table_result = fibonacci_rpc_master.call(message_sent_serialized)
                table_result = fibonacci_rpc_sync.call(message_sent_serialized)
                print(table_result)  

            if 'clear' in request.json:

                message_sent = list( ["write" , "ride", "clear"] )
                print('message_sent  ',message_sent)
                message_sent_serialized = pickle.dumps(message_sent)
                print('message_sent_serialized  ',message_sent_serialized)
                
                table_result = fibonacci_rpc_master.call(message_sent_serialized)
                table_result = fibonacci_rpc_sync.call(message_sent_serialized)
                print(table_result)  


        return Response(json.dumps(dict()),status=200)
    #except:
    #    print('EXCEPT ERROR IN WRITE !!')
    #    return Response(json.dumps(dict()),status=500)   

@app.route('/api/v1/_count',methods=['GET','DELETE'])
def getCount():
    try:
        if request.method=='GET':
            return Response(json.dumps(list([v.value]),default=str),status=200)
            #return Response(json.dumps(v.value),status=200)
        if request.method=='DELETE':
            resetCount(v,lock)
            return Response(json.dumps(dict()),status=200)

    except:
        return Response(json.dumps(dict()),status=405)     

@app.route('/api/v1/db/main',methods=['GET'])
def sendHello():
    
    return "Hello world from Database"


@app.route('/api/v1/crash/master',methods=['POST'])
def crash_master():
    print("CRASHING MASTER!!")
    current_master_id_name_pid = str( zk.get(master_path)[0].decode("utf-8")).split(" ")
    current_master_name = current_master_id_name_pid[1]
    client.containers.get(current_master_name).stop()
    client.containers.get(current_master_name).remove()

    zk.exists(master_path, watch = watch_master_node)
    zk.set(master_path, b"")

    time.sleep(0.25)
    #return Response(json.dumps(current_master_name),status=200)
    return Response(json.dumps(dict()),status=200)



@app.route('/api/v1/crash/slave',methods=['POST'])
def crash_slave():

    global slave_name_counter
    print("CRASHING SLAVE!!")

    slave_list = zk.get_children(slave_path)
    slave_container_id_name_pid=[]
    for slave in slave_list:
        data, stat = zk.get(slave_path + "/" + slave)
        data = str( data.decode("utf-8") ).split(" ")
        slave_container_id_name_pid.append(data)

    max_container_id = -1
    max_container_name = -1
    max_container_pid = -1

    for i in slave_container_id_name_pid:
        if int( i[2] ) > int( max_container_pid ):
            max_container_id = i[0]
            max_container_name = i[1]
            max_container_pid = i[2]

    client.containers.get(max_container_name).stop()
    client.containers.get(max_container_name).remove()
    zk.delete(slave_path + "/" + max_container_name, recursive=True)
    print("Deleted container\t",max_container_name)

    container_name = str("ws_"+str(slave_name_counter))
    slave_name_counter += 1
    #client.containers.run("debian:stretch-slim", name=container_name, detach=True, tty=True)
    client.containers.run("worker:v1", name=container_name, detach=True)
    #client.containers.get(new_worker_name).exec_run("python3 Cloud-Computing-Course/Database/Database/rpc_server_database.py 1", detach =True)
    client.containers.get(container_name).exec_run("python3 Cloud-Computing-Course/Database/Database/rpc_server_database.py 1", detach =True)

    container_id = client.containers.get(container_name).id
    container_name = client.containers.get(container_name).name
    stream = os.popen("sudo docker inspect --format '{{ .State.Pid }}' " +'"' + str(container_id) + '"' )
    container_pid = stream.read()
    container_pid = int(container_pid)
    slave_container_id_name_pid.append( [str(container_id),str(container_name),str(container_pid)] )

    zk.create(slave_path + "/" + str(container_name))
    slave_container_id_name_pid_string = str(container_id)+" "+str(container_name)+" "+str(container_pid)
    zk.set(slave_path + "/" + str(container_name), slave_container_id_name_pid_string.encode('utf-8'))

    #return Response(json.dumps(int(container_pid)),status=200)
    return Response(json.dumps(dict()),status=200)


@app.route('/api/v1/worker/list',methods=['GET'])
def worker_list():
    print("Worker List ")
    slave_list = zk.get_children(slave_path)
    slave_container_id_name_pid=[]
    for slave in slave_list:
        data, stat = zk.get(slave_path + "/" + slave)
        data = str( data.decode("utf-8") ).split(" ")
        slave_container_id_name_pid.append(data)

    pid_list = [int( i[2] ) for i in slave_container_id_name_pid]
    pid_list = sorted( pid_list )


    return Response(json.dumps( pid_list ),status=200)
