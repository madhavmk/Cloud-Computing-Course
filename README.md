# Cloud-Computing-Course

Project source code for Cloud Computing course (UE17CS352)

Team name : CC_0227_1123_1139_1526

# External Python Requirements

pip3 install psycopg2-binary

pip3 install waitress flask flask-sqlalchemy flask-cors requests

pip3 install pandas

# Excecution commands

## On Users Instance

sudo python3 Cloud-Computing-Course/Assignment\ 3/User/waitress_server.py

## On Rides Instance

sudo python3 Cloud-Computing-Course/Assignment\ 3/Ride/waitress_server.py

## On Orchestrator instance

sudo docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3.6-management-alpine

sudo docker run -p 2181:2181 -p 2888:2888 -p 3888:3888 --name zookeeper --restart always -d zookeeper

sudo python3 Cloud-Computing-Course/Database/Database/waitress_server.py


