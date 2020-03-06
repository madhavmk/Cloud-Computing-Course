from flask import Flask, jsonify,request, Response
from flask_cors import CORS 
from flask_sqlalchemy import SQLAlchemy


app=Flask(__name__)
app.debug = True
print('Started User Server !!')

@app.route('/api/v1/users',methods=['GET'])
def greeting():
    print('Request to User made')

    return Response("Hello from User ")