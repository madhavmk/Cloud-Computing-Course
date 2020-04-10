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

#!/usr/bin/env python
import pika
import sys

import datetime

import pickle


app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Iusepostgres@321@52.73.30.120/Cloud_Computing_Assignment'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Iusepostgres@321@localhost/Cloud_Computing_Assignment'
db=SQLAlchemy(app)
CORS(app)
app.debug = True
print('Connected to DB !!')


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






if(int(sys.argv[1]) == 0):

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='52.73.30.120'))

    channel = connection.channel()

    channel.queue_declare(queue='rpc_queue_master')

    def func_master(n):
        table = str(n[1])
        if(table == "user"):
            command = str(n[2])
            if(command == "insert"):
                new_user = n[3]
                db.session.add(new_user)
                db.session.commit()
            elif(command == "delete"):
                username = n[3]
                User.query.filter(User.username == username).delete()
                db.session.commit()
            elif(command=="clear"):
                db.session.query(User).delete()
                db.session.commit()
            else:
                pass
        elif(table == "ride"):
            command = str(n[2])
            if(command == "insert"):
                new_ride = n[3]
                db.session.add(new_ride)
                db.session.commit()
            elif(command == "update"):
                RideID = n[3]
                Username = n[4]

                ride_to_update=Ride.query.filter(Ride.RideID == RideID).all()
                print('before update users ',ride_to_update[0].Users)
                if ride_to_update[0].Users=="":
                    ride_to_update[0].Users=Username
                else:
                    ride_to_update[0].Users=ride_to_update[0].Users+";"+Username
                print('after update users ',ride_to_update[0].Users)
                db.session.commit()

            elif(command == "delete"):
                RideID = n[3]
                Ride.query.filter(Ride.RideID == RideID).delete()
                db.session.commit()
            elif(command=="clear"):
                db.session.query(Ride).delete()
                db.session.commit()
            else:
                pass
        else:
            pass

        return " something from master "



    def on_request_master(ch, method, props, body):
        
        print('body  ',body, '  type  ',type(body))

        #print('pickle.loads(body)  ',, '  type  ',type(body))
        n = pickle.loads(body)



        print(" [.] func_master(%r)" % n)
        response = func_master(n)

        ch.basic_publish(exchange='',
                        routing_key=props.reply_to,
                        properties=pika.BasicProperties(correlation_id = \
                                                            props.correlation_id),
                        body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='rpc_queue_master', on_message_callback=on_request_master)

    print('Started Master Worker !')
    print(" [x] Awaiting RPC requests")
    channel.start_consuming()

if(int(sys.argv[1]) == 1):
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='52.73.30.120'))

    channel = connection.channel()
    
    channel.queue_declare(queue='rpc_queue_slave')
    channel.queue_declare(queue='rpc_queue_sync')
    
    channel.basic_qos(prefetch_count=1)    
    

    def func_slave(n):
        command =[str(i) for i in n.split("$")]
        print('command ',command)
        if(command[1]=="user"):
            table_result = User.query.filter().all()
            table_result_serialized=pickle.dumps(table_result)
            return table_result_serialized
        elif(command[1]=="ride"):
            table_result = Ride.query.filter().all()
            table_result_serialized=pickle.dumps(table_result)
            return table_result_serialized
        elif(command[1]=="area"):
            table_result = Area.query.filter().all()
            table_result_serialized=pickle.dumps(table_result)
            return table_result_serialized
        else:
            return list([])


        """
        if n == 0:
            return 0
        elif n == 1:
            return 1
        else:
            return func(n - 1) + func(n - 2)
        """
        return " something from slave "


    def func_sync(n):
        """
        if n == 0:
            return 0
        elif n == 1:
            return 1
        else:
            return func(n - 1) + func(n - 2)
        """
        return " something from sync "


    def on_request_slave(ch, method, props, body):
        n = str(body,"utf-8")
        print(" [.] func_slave(%s)" % n)
        #response = str(func_slave(n)) + " from SLAVE"
        response = func_slave(n)
        print("response type ",type(response),' response ',response)

        ch.basic_publish(exchange='',
                        routing_key=props.reply_to,
                        properties=pika.BasicProperties(correlation_id = \
                                                            props.correlation_id),
                        #body=str(response))
                        body=response)
        ch.basic_ack(delivery_tag=method.delivery_tag)


    def on_request_sync(ch, method, props, body):
        n = str(body,"utf-8")

        print(" [.] func_sync(%s)" % n)
        response = str(func_sync(n)) + " from SYNC"

        ch.basic_publish(exchange='',
                        routing_key=props.reply_to,
                        properties=pika.BasicProperties(correlation_id = \
                                                            props.correlation_id),
                        body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)


    channel.basic_consume(queue='rpc_queue_slave', on_message_callback=on_request_slave)
    channel.basic_consume(queue='rpc_queue_sync', on_message_callback=on_request_sync)

    
    print('Started Slave Worker !')
    print(" [x] Awaiting RPC requests")
    channel.start_consuming()