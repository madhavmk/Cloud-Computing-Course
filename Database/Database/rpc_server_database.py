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

# 

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Iusepostgres@321@52.73.30.120/Cloud_Computing_Assignment' # Connection details database, postgres username, password, IP address of server, Database name 
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





# If console argument passed is 0, run master worker code
if(int(sys.argv[1]) == 0):

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='52.73.30.120', heartbeat=0)) # Connects to Pika connection on Orhestrator IP address. Also heartbeat 0 means that the TCP connection will never close even when idle.

    channel = connection.channel()

    channel.queue_declare(queue='rpc_queue_master') # Connects to the master Queue

    def func_master(n): # Function to call when Write request arrives.
        table = str(n[1])
        if(table == "user"):
            command = str(n[2])
            if(command == "insert"):
                new_user = n[3]
                db.session.add(new_user)
                db.session.commit() # Saves changes to DB
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
                RideID = n[3] # Which row to place username into
                Username = n[4] # Username to add into 

                ride_to_update=Ride.query.filter(Ride.RideID == RideID).all()
                if ride_to_update[0].Users=="":
                    ride_to_update[0].Users=Username
                else:
                    ride_to_update[0].Users=ride_to_update[0].Users+";"+Username
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

        n = pickle.loads(body) # Convert from Byte data to Python object.



        print(" [.] func_master(%r)" % n)
        response = func_master(n)

        ch.basic_publish(exchange='', # Do not use a named queue to reply message back.
                        routing_key=props.reply_to,  # Reply back to the exact process that sent the message using ID
                        properties=pika.BasicProperties(correlation_id = \
                                                            props.correlation_id),
                        body=str(response)) # body of the reply message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)  # Always allow only 1 message to be processed at a time. Wait for a single Acknowledgement to process a new one.
    channel.basic_consume(queue='rpc_queue_master', on_message_callback=on_request_master)

    print('Started Master Worker !')
    print(" [x] Awaiting RPC requests")
    channel.start_consuming()


# If console argument passed is 1, run slave worker code
if(int(sys.argv[1]) == 1):
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='52.73.30.120', heartbeat=0))

    channel = connection.channel()
    
    channel.queue_declare(queue='rpc_queue_slave') # Connects to the slave Queue
    channel.queue_declare(queue='rpc_queue_sync') # Connects to the sync Queue
    
    channel.basic_qos(prefetch_count=1) # Stop delivering messages unless the one beiing processed in Acknowledged back to the reciever

    def func__sync(n):
        return " something from slave "    


    def func_slave(n): # Function to call when Read request arrives.
        command =[str(i) for i in n.split("$")]
        print('command ',command)
        if(command[1]=="user"):
            table_result = User.query.filter().all()  # table_result is a list of User objects
            table_result_serialized=pickle.dumps(table_result)  # pickle dumps is used to convert from Python to Bytes.
            return table_result_serialized # Return that Byte data
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

        return " something from slave "


    def func_sync(n): # Function to call when Write sync arrives.
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
                if ride_to_update[0].Users=="":
                    ride_to_update[0].Users=Username
                else:
                    ride_to_update[0].Users=ride_to_update[0].Users+";"+Username
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


    def on_request_slave(ch, method, props, body):
        n = str(body,"utf-8")  # Decode the body of the message using utf-8 decoding.
        print(" [.] func_slave(%s)" % n)
        response = func_slave(n)
        print("response type ",type(response),' response ',response)

        ch.basic_publish(exchange='',
                        routing_key=props.reply_to,
                        properties=pika.BasicProperties(correlation_id = \
                                                            props.correlation_id),
                        
                        body=response)
        ch.basic_ack(delivery_tag=method.delivery_tag)


    def on_request_sync(ch, method, props, body):
        #n = str(body,"utf-8")
        n = pickle.loads(body)
        print(" [.] func_sync(%s)" % n)
        response = func__sync(n)

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