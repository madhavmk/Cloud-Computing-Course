from flask import Flask, jsonify,request, Response
from flask_cors import CORS 
from flask_sqlalchemy import SQLAlchemy
from multiprocessing import Value

counter = Value('i', 0)

app=Flask(__name__)
app.debug = True
print('Started Ride Server !!')

@app.route('/api/v1/_count',methods=['GET']):
def getCount():
    try:
        return Response(json.dumps(count=counter.value),status=200)
    except:
        return Response(json.dumps(dict()),status=405)

@app.route('/api/v1/_count',methods=['DELETE']):
def getCount():
    try:
        with counter.get_lock():
            counter.value=0
        return Response(json.dumps(dict()),status=200)
    except:
        return Response(json.dumps(dict()),status=405)


@app.route('/api/v1',methods=['GET'])
def greeting():
    with counter.get_lock():
        counter.value += 1
    print('Request to Ride made')

    return Response("Hello from Ride ")