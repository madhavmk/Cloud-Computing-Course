import psycopg2
print('trying connection')
db = psycopg2.connect("dbname='Cloud_Computing_Assignment' user='postgres' host='52.73.30.120' password='Iusepostgres@321'")
print('success')
#Public IP
#db = psycopg2.connect("dbname='Cloud_Computing_Assignment' user='postgres' host='52.73.30.120' password='Iusepostgres@321'")

#Private IP 10 times faster ping
#db = psycopg2.connect("dbname='Cloud_Computing_Assignment' user='postgres' host='172.31.88.235' password='Iusepostgres@321'")