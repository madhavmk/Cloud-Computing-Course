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
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Iusepostgres@321@localhost/cloud_computing_assignment_user'
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

"""
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
"""

try:
    User.__table__.create(db.session.bind)
except:
    pass
"""
try:
    Ride.__table__.create(db.session.bind)
except:
    pass
"""

"""
#task 4 done
@app.route('/api/v1/rides',methods=['GET'])
def readRide():
    try:
        try:
            source = int(request.args.get('source'))
            destination = int(request.args.get('destination'))
        except:
            print('no source or destination given')
            return(Response(json.dumps(dict()),status=400)) 

        print(' source ',source,' destination ',destination)



        url_request = "http://localhost:80/api/v1/db/read"
        data_request = {'table' : 'ride', 'columns': '', 'where':'' }
        headers_request = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(url_request,data=json.dumps(data_request),headers=headers_request)
        response_list=response.json()
        filtered_list=[]
        for row in response_list:
            RideID=int(row[0])
            CreatedBy=str(row[1])
            Users=str(row[2])
            Timestamp=row[3]
            Source=int(row[4])
            Destination=int(row[5])
            print(list([RideID,CreatedBy,Users,Timestamp,Source,Destination]))
            if(Source==source and Destination==destination):
                #filtered_list.append(json.dumps({"rideId" : int(RideID),"username":str(CreatedBy),"timestamp":str(Timestamp)},default=str))
                temp_dict=dict()
                temp_dict["rideId"]=int(RideID)
                temp_dict["username"]=str(CreatedBy)
                print('point 1')
                print('TS before ',Timestamp)
                TimestampObject= datetime.datetime.strptime(Timestamp,'%Y-%m-%d %H:%M:%S')
                print('TS Object  ',TimestampObject)
                Timestamp_string=TimestampObject.strftime('%d-%m-%Y:%S:%M:%H')
                print('TS after ',Timestamp_string)
                temp_dict["timestamp"]=str(Timestamp_string)
                
                filtered_list.append(temp_dict)
        print('filtered_list ',filtered_list)

        if len(filtered_list)>0:
            #return Response(json.dumps(filtered_list,default=str),status=200)
            return Response(json.dumps(filtered_list,default=str),status=200)
        else:
            return '',204
    except:
        print('EXCEPT ERROR IN TASK 4 !!')
        return Response(json.dumps(dict()),status=500)
"""

"""
#TASK 3 DONE
@app.route('/api/v1/rides',methods=['POST'])
def addRides():
    try:
        username = request.json['created_by']
        print('username received ',username)
        timestamp = request.json['timestamp']
        print('timestamp received ',timestamp)
        source = request.json['source']
        print('source received ',source,' type ',type(source))
        destination = request.json['destination']
        print('destination received ',destination,' type ',type(destination))

        #print('start')
        if(int(source)==int(destination)):
            return Response(json.dumps(dict()),status=400)
        
        if(int(source)<1 or int(source) >198):
            return Response(json.dumps(dict()),status=400)
        
        if(int(destination)<1 or int(destination) >198):
            return Response(json.dumps(dict()),status=400)
        
        url_request = "http://localhost:80/api/v1/db/read"
        data_request = {'table' : 'user', 'columns': '', 'where':'' }
        headers_request = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(url_request,data=json.dumps(data_request),headers=headers_request)
        response_list=response.json()
        #print('response list ',response_list)

        username_list=[]
        for row in response_list:
            username_list.append(str(row[1]))

        if str(username) not in username_list:
            print('username not in user list')
            return Response(json.dumps(dict()),status=400)

        try:
            TimestampObject= datetime.datetime.strptime(timestamp,'%d-%m-%Y:%S-%M-%H')
        except:
            print('Invalid Timestamp')
            return Response(json.dumps(dict()),status=400)    
        

        url_request = "http://localhost:80/api/v1/db/write"
        insert_data_request=str(username)+';'+str(timestamp)+';'+str(source)+';'+str(destination)
        #print('insert data request')
        data_request = {'table' : 'ride', 'insert': str(insert_data_request), 'column':6 }
        #print('data request')
        headers_request = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        #print('header request')
        response = requests.post(url_request,data=json.dumps(data_request),headers=headers_request)
        print('response ',response)

        return Response(json.dumps(dict()),status=201)

    except:
        print('EXCEPT TASK 3 ERROR !!')
        return Response(json.dumps(dict()),status=500)        
"""


##TASK 1 DONE
@app.route('/api/v1/users',methods=['PUT'])
def addUser():
    incrementCount(v,lock)
    try:
        username = request.json['username']
        #print('username received ',username)
        password = request.json['password']
        #print('password received ',password)


        if(len(password)!=40 or all(c in string.hexdigits for c in password)==False):
            print('Password Invalid !!')
            return Response(json.dumps(dict()), status=400)

        #url_request = "http://localhost:80/api/v1/db/read"
        url_request = "http://52.73.30.120/api/v1/db/read"
        data_request = {'table' : 'user', 'columns': '', 'where':'' }
        headers_request = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(url_request,data=json.dumps(data_request),headers=headers_request)
        response_list=response.json()
        print('response list ',response_list)

        for row in response_list:
            if str(username)==str(row[1]):
                print('Duplicate username !!')
                return Response(json.dumps(dict()), status=400)

        #print(response_list)



        #url_request = "http://localhost:80/api/v1/db/write"
        url_request = "http://52.73.30.120/api/v1/db/write"
        insert_data_request=str(username)+';'+str(password)
        data_request = {'table' : 'user', 'insert': str(insert_data_request), 'column':6 }
        headers_request = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(url_request,data=json.dumps(data_request),headers=headers_request)
        #print(response)


        return Response(json.dumps(dict()),status=201)
    except:
        print('EXCEPT TASK 1 ERROR')
        return Response(json.dumps(dict()),status=500)        



#TASK 2 
@app.route('/api/v1/users/<username>',methods=['DELETE'])
def deleteUser(username):

    incrementCount(v,lock)

    print('\n\nDElETING USER')
    username=str(username)
    print('username ',username)

    #url_request = "http://localhost:80/api/v1/db/read"
    url_request = "http://52.73.30.120/api/v1/db/read"
    data_request = {'table' : 'user', 'columns': '', 'where':'' }
    headers_request = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    response = requests.post(url_request,data=json.dumps(data_request),headers=headers_request)
    response_list=response.json()
    print('response list ',response_list)
    username_list=[]
    for row in response_list:
        username_list.append(str(row[1]))
    print('username list ',username_list)
    if str(username) not in username_list:
        print('username NOT present')
        return Response(json.dumps(dict()), status=400)

    #url_request = "http://localhost:80/api/v1/db/write"
    url_request = "http://52.73.30.120/api/v1/db/write"
    data_request = {'table' : 'user', 'delete' : username }
    headers_request = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    response = requests.post(url_request,data=json.dumps(data_request),headers=headers_request)

    return Response(json.dumps(dict()),status=200)


"""
@app.route('/api/v1/rides/<rideID_query>',methods=['GET'])
def readRideID(rideID_query):
    print('\n\nGETTING RIDE DETAILS')
    rideID_query=int(rideID_query)
    print('ride id ',rideID_query)
    url_request = "http://localhost:80/api/v1/db/read"
    data_request = {'table' : 'ride', 'columns': '', 'where':'' }
    headers_request = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    response = requests.post(url_request,data=json.dumps(data_request),headers=headers_request)
    response_list=response.json()
    filtered_list=[]
    for row in response_list:
        RideID=int(row[0])
        CreatedBy=str(row[1])
        Users=str(row[2])
        Timestamp=row[3]
        Source=int(row[4])
        Destination=int(row[5])
        print(list([RideID,CreatedBy,Users,Timestamp,Source,Destination]))
        if(rideID_query==RideID):
            #filtered_list.append(list([RideID,CreatedBy,Users,Timestamp,Source,Destination]))
            filtered_list.append(json.dumps({"rideId":RideID,"Created_by":CreatedBy,"users":list(Users.split(";")),"Timestamp": Timestamp,"source":Source,"destination":Destination}))
    print('filtered_list ',filtered_list)
    
    return Response(filtered_list,status=200)
"""

"""

#Task 7
@app.route('/api/v1/rides/<rideID_query>',methods=['DELETE'])
def deleteRideID(rideID_query):
    print('\n\n DELETING RIDE !')
    rideID_query=int(rideID_query)
    print('ride id',rideID_query)

    url_request = "http://localhost:80/api/v1/db/write"
    data_request = {'table' : 'ride', 'delete' : str(rideID_query) }
    headers_request = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    response = requests.post(url_request,data=json.dumps(data_request),headers=headers_request)

    return Response(json.dumps(dict()),status=200)

"""

"""

@app.route('/api/v1/rides/<rideID_query>',methods=['POST'])
def updateRideUsers(rideID_query):
    print('UPDATING RIDE')
    rideID_query=int(rideID_query)
    username = str(request.json['username'])
    print('ride id ',rideID_query,' username ',username)
    url_request = "http://localhost:80/api/v1/db/write"
    data_request = {'table' : 'ride', 'update' : str(rideID_query)+';'+str(username) }
    headers_request = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    response = requests.post(url_request,data=json.dumps(data_request),headers=headers_request)

    return Response(json.dumps(dict()),status=200)
"""


#Assignment 2 task
@app.route('/api/v1/users',methods=['GET'])
def readAllUsers():
    incrementCount(v,lock)
    try:
        
        try:
            print(str(request.headers['Origin']))
        except:
            print("Could NOT read Origin!!")

        #url_request = "http://localhost:80/api/v1/db/read"
        url_request = "http://52.73.30.120/api/v1/db/read"
        data_request = {'table' : 'user', 'columns': '', 'where':'' }
        headers_request = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(url_request,data=json.dumps(data_request),headers=headers_request)
        response_list=response.json()
        response_list = [str(i[1]) for i in response_list]
        print('response list ',response_list)

        if len(response_list)==0:
            return '',204
        else:
            return Response(json.dumps(response_list,default=str),status=200)

    except:
        print('EXCEPT ERROR IN READ ALL USERS !!')
        return Response(json.dumps(dict()),status=400)   

#Assignment 2 Task
@app.route('/api/v1/db/clear',methods=['POST'])
def clearTables():
    incrementCount(v,lock)
    try:
        #url_request = "http://localhost:80/api/v1/db/write"
        url_request = "http://52.73.30.120/api/v1/db/write"
        data_request = {'table' : 'user', 'clear' : 'placeholder text' }
        headers_request = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(url_request,data=json.dumps(data_request),headers=headers_request)
        return Response(json.dumps(dict()),status=200)

        """
        url_request = "http://localhost:80/api/v1/db/write"
        data_request = {'table' : 'ride', 'clear' : 'placeholder text' }
        headers_request = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(url_request,data=json.dumps(data_request),headers=headers_request)
        """
    except:
        print('EXCEPT ERROR IN CLEAR User TABLES !!')
        return Response(json.dumps(dict()),status=400) 

    

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
            return Response(json.dumps(list([int(v.value)]),default=str),status=200)
        if request.method=='DELETE':
            resetCount(v,lock)
            return Response(json.dumps(dict()),status=200)

    except:
        return Response(json.dumps(dict()),status=405)        


@app.route('/api/v1/users/main',methods=['GET'])
def sendHello():
    incrementCount(v,lock)
    return "Hello from User"

#if __name__ == '__main__':
#    app.run(host="0.0.0.0",port=80)
