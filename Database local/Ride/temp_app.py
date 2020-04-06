from flask import Flask, jsonify,request, Response
from flask_cors import CORS 
from flask_sqlalchemy import SQLAlchemy
from multiprocessing import Process, Value, Lock
import json

def incrementCount(val, lock):
    with lock:
        val.value += 1
def resetCount(val,lock):
    with lock:
        val.value = 0


v = Value('i', 0)
lock = Lock()
'''
incrementCount(v,lock)
print(v.value)
'''

app=Flask(__name__)
app.debug = True
print('Started Ride Server !!')

@app.route('/api/v1/_count',methods=['GET','DELETE'])
def getCount():
    print('start')
    try:
        if request.method=='GET':
            return Response(json.dumps(v.value),status=200)
        if request.method=='DELETE':
            resetCount(v,lock)
            return Response(json.dumps(dict()),status=200)

    except:
        return Response(json.dumps(dict()),status=405)


@app.route('/api/v1',methods=['GET'])
def greeting():
    incrementCount(v,lock)
    print('Request to Ride made')

    return Response("Hello from Ride ")