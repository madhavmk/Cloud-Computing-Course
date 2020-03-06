from flask import Flask, jsonify,request, Response
from flask_cors import CORS 
from flask_sqlalchemy import SQLAlchemy


app=Flask(__name__)
app.debug = True
print('Started Ride Server !!')

@app.route('/api/v1',methods=['GET'])
def greeting():
    print('Request to Ride made')

    return Response("Hello from Ride ")