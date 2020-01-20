from flask import Flask, jsonify,request, Response
from flask_cors import CORS 
from flask_sqlalchemy import SQLAlchemy
import string
import csv
import pandas as pd


#class User(db.Model):

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Iusepostgres@321@localhost/Cloud_Computing_Assignment'
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

try:
    Area.__table__.create(db.session.bind)
except:
    pass

with open('AreaNameEnum.csv', 'r') as file:
    data_df = pd.read_csv('AreaNameEnum.csv')
    #print(data_df)
    for index,row in data_df.iterrows():
        #print(row['Area No'],row['Area Name'])
        new_area = Area(row['Area No'],row['Area Name'])
        db.session.add(new_area)
    db.session.commit()

class User(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String, unique=True)
    password=db.Column(db.String)

    def __init__(self,username,password):
        self.username=username
        self.password=password

    def __repr__(self):
        return (str(self.username) + '\t' + str(self.password))

try:
    User.__table__.create(db.session.bind)
except:
    pass

class Ride(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    source=db.Column(db.Integer)
    destination=db.Column(db.Integer)
    timestamp=db.

    def __init__(self,username,password):
        self.username=username
        self.password=password

    def __repr__(self):
        return (str(self.username) + '\t' + str(self.password))

try:
    User.__table__.create(db.session.bind)
except:
    pass

@app.route('/api/v1/users',methods=['PUT'])
def addUser():
    username = request.args.get('username',None)
    print('username received ',username)
    password = request.args.get('password',None)
    print('password received ',password)
    if(username==None or password==None):
        content={'Username or Password field empty !!'}
        print(content)
        return Response(content,status=400)
    if(len(password)!=40 or all(c in string.hexdigits for c in password)==False):
        content={'Password Invalid !!'}
        print(content)
        return Response(content, status=400)
    
    new_user = User(username,password)
    db.session.add(new_user)
    db.session.commit()
    print('Added to DB \t' + str(username) + '\t' + str(password))
    return Response(str(username) + "\t" + str(password),status=200)

@app.route('/api/v1/users/<username>',methods=['DELETE'])
def deleteUser(username):
    #username = str(request.args.get('username',None))
    print('username received ',username)
    query_result = User.query.filter(User.username == username)
    print('Query type ',query_result.all())
    #print('Query result \t'+str(query_result))
    query_result.delete()
    db.session.commit()
    #print('Deleted Query\t'+query_result.id+"\t"+query_result.username+"\t"+query_result.password)
    return Response('Deleted Query Result\t'+str(query_result),status=200)




    





tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol', 
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web', 
        'done': False
    }
]



if __name__ == '__main__':
    app.run(debug=True)