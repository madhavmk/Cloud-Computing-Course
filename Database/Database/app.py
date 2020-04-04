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



def incrementCount(val, lock):
    with lock:
        val.value += 1
def resetCount(val,lock):
    with lock:
        val.value = 0


v = Value('i', 0)
lock = Lock()


app=Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Iusepostgres@321@localhost/cloud_computing_assignment_ride'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Iusepostgres@321@localhost/Cloud_Computing_Assignment'
db=SQLAlchemy(app)
CORS(app)
app.debug = True
print('Connected to DB !!')

counter = Value('i', 0)

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


    

@app.route('/api/v1/db/read',methods=['POST'])
def dbRead():
    table=request.json['table']
    columns=request.json['columns']
    where=request.json['where']
    if(table=="user"):
        table_result = User.query.filter().all()
        table_result_list=[]
        for i in table_result:
            table_result_list.append(i.representation())
    elif(table=="ride"):
        table_result = Ride.query.filter().all()
        table_result_list=[]
        for i in table_result:

            table_result_list.append(i.representation())
    elif(table=="area"):
        table_result = Area.query.filter().all()
        table_result_list=[]
        for i in table_result:
            table_result_list.append(i.representation())
    else:
        table_result_list=[]
    print(table_result_list)
    return Response(json.dumps(table_result_list,default=str),status=200)

@app.route('/api/v1/db/write',methods=["POST"])
def dbWrite():
    try:
        table=request.json['table']

        if(table=="user"):
            if 'insert' in request.json:
                insert=request.json['insert']
                insert_list=insert.split(";")
                username=str(insert_list[0])
                password=str(insert_list[1])
                new_user = User(username,password)
                db.session.add(new_user)
                db.session.commit()
            
            if 'delete' in request.json:
                delete=request.json['delete']
                username=str(delete)
                User.query.filter(User.username == username).delete()
                db.session.commit()

            if 'clear' in request.json:
                db.session.query(User).delete()
                db.session.commit()


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
                db.session.add(new_ride)
                db.session.commit()
            
            if 'update' in request.json:
                update_list=request.json['update'].split(";")
                RideID=int(update_list[0])
                Username=str(update_list[1])
                ride_to_update=Ride.query.filter(Ride.RideID == RideID).all()
                print('before update users ',ride_to_update[0].Users)
                if ride_to_update[0].Users=="":
                    ride_to_update[0].Users=Username
                else:
                    ride_to_update[0].Users=ride_to_update[0].Users+";"+Username
                print('after update users ',ride_to_update[0].Users)
                db.session.commit()

            if 'delete' in request.json:
                delete=request.json['delete']
                RideID=int(delete)
                Ride.query.filter(Ride.RideID == RideID).delete()
                db.session.commit()

            if 'clear' in request.json:
                db.session.query(Ride).delete()
                db.session.commit()

        return Response(json.dumps(dict()),status=200)
    except:
        print('EXCEPT ERROR IN WRITE !!')
        return Response(json.dumps(dict()),status=500)   

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

#if __name__ == '__main__':
#    app.run(host="0.0.0.0",port=80)
