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

from multiprocessing import Process, Value, Lock
#Install psycopg2 or psycopg2-binary
#Install waitress

import pika
import uuid
import pickle

###########################################################

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Iusepostgres@321@52.73.30.120/Cloud_Computing_Assignment'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Iusepostgres@321@localhost/Cloud_Computing_Assignment'
db=SQLAlchemy(app)
CORS(app)
app.debug = True
print('Connected to DB !!')


def incrementCount(val, lock):
    with lock:
        val.value += 1
def resetCount(val,lock):
    with lock:
        val.value = 0

v = Value('i', 0)
lock = Lock()

counter = Value('i', 0)


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
            pika.ConnectionParameters(host='52.73.30.120'))

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
            pika.ConnectionParameters(host='52.73.30.120'))

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
            pika.ConnectionParameters(host='52.73.30.120'))

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
            body=str(n))
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
                print(table_result)
            
            if 'delete' in request.json:
                delete=request.json['delete']
                username=str(delete)

                message_sent = list( ["write" , "user", "delete" , username] )
                print('message_sent  ',message_sent)

                message_sent_serialized = pickle.dumps(message_sent)
                print('message_sent_serialized  ',message_sent_serialized)
                
                table_result = fibonacci_rpc_master.call(message_sent_serialized)
                print(table_result)



            if 'clear' in request.json:

                message_sent = list( ["write" , "user", "clear"] )
                print('message_sent  ',message_sent)

                message_sent_serialized = pickle.dumps(message_sent)
                print('message_sent_serialized  ',message_sent_serialized)
                
                table_result = fibonacci_rpc_master.call(message_sent_serialized)
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
                print(table_result) 



            if 'delete' in request.json:
                delete=request.json['delete']
                RideID=int(delete)

                message_sent = list( ["write" , "ride", "delete" , RideID] )
                print('message_sent  ',message_sent)

                message_sent_serialized = pickle.dumps(message_sent)
                print('message_sent_serialized  ',message_sent_serialized)
                
                table_result = fibonacci_rpc_master.call(message_sent_serialized)
                print(table_result)  

            if 'clear' in request.json:

                message_sent = list( ["write" , "ride", "clear"] )
                print('message_sent  ',message_sent)
                message_sent_serialized = pickle.dumps(message_sent)
                print('message_sent_serialized  ',message_sent_serialized)
                
                table_result = fibonacci_rpc_master.call(message_sent_serialized)
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
    incrementCount(v,lock)
    return "Hello world from Database"
