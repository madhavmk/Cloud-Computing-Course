import kazoo
from kazoo.client import KazooClient
from kazoo.client import KazooState

import docker

import os
import time

def my_zookeeper_listener(state):  #KEEPS WATCH ON ZOOKEEPER STATE
    if state == KazooState.LOST:
        print("\n\tSESSION LOST\n")
    elif state == KazooState.SUSPENDED:
        print("\n\tSESSION SUSPENDED\n")
    else:
        print("\n\tSESSION CONNECTED / RECONNECTED\n")

client = docker.from_env()

zk = KazooClient(hosts='127.0.0.1:2181')
zk.add_listener(my_zookeeper_listener)

zk.start()

slave_path = "/slave"
master_path = "/master"


if zk.exists(master_path):
    print("master path does exist. Deleting and Creating path")
    zk.delete(master_path, recursive=True)
    zk.create(master_path, ephemeral=False)
else:
    print("master path does NOT exist. Creating path")
    zk.create(master_path, ephemeral=False)

if zk.exists(slave_path):
    print("slave path does exist. Deleting and Creating path")
    zk.delete(slave_path, recursive=True)
    zk.create(slave_path, ephemeral=False)
else:
    print("slave path does NOT exist. Creating path")
    zk.create(slave_path, ephemeral=False)


slave_name_counter = 0
number_slaves_to_spawn = 10

for i in range(number_slaves_to_spawn):
    #client.containers.run("worker:v1", name=new_worker_name, detach=True)
    container_name = str("ws_"+str(i))
    client.containers.run("debian:stretch-slim", name=container_name, detach=True, tty=True)
    #client.containers.get(new_worker_name).exec_run("python3 Cloud-Computing-Course/Database/Database/rpc_server_database.py 1", detach =True)
    client.containers.get(container_name).exec_run("ls", detach =True)
    print("STARTED Slave container\t", container_name)

    slave_name_counter += 1


#Adds slave and master to znodes
running_containers = client.containers.list() # running_containers = client.containers.list(all=True)
slave_container_id_name_pid=[]
#master_container_id_name_pid=[]
for i in running_containers:
    if str(i.name).startswith("ws"):
        container_id = i.id
        container_name = i.name
        stream = os.popen("sudo docker inspect --format '{{ .State.Pid }}' " +'"' + str(container_id) + '"' )
        #DOCKER IP ADDRESS sudo sudo docker inspect -f '{{.NetworkSettings.IPAddress }}' wm01
        container_pid = stream.read()
        container_pid = int(container_pid)
        slave_container_id_name_pid.append( [str(container_id),str(container_name),str(container_pid)] )

        zk.create(slave_path + "/" + str(container_name))
        slave_container_id_name_pid_string = str(container_id)+" "+str(container_name)+" "+str(container_pid)
        zk.set(slave_path + "/" + str(container_name), slave_container_id_name_pid_string.encode('utf-8'))


zk.set(master_path, b"")

print("Initial slave_container_id_name_pid\t",slave_container_id_name_pid)

@zk.ChildrenWatch(slave_path)
def watch_slave_node(children):
    print("\nSlave node change !! Current children:\t", children)

#@zk.DataWatch(master_path)
def watch_master_node(CHANGED):
    print("Master Node data Change !! ")
    print("Leader Election !!")
    slave_list = zk.get_children(slave_path)
    slave_container_id_name_pid=[]
    for slave in slave_list:
        data, stat = zk.get(slave_path + "/" + slave)
        data = str( data.decode("utf-8") ).split(" ")
        slave_container_id_name_pid.append(data)
    
    if( len(slave_container_id_name_pid) == 1):
        print("ELECTION CANCEL !! No Slaves to pick from")
    
    else:
        max_container_id = -1
        max_container_name = -1
        max_container_pid = -1

        for i in slave_container_id_name_pid:
            if int( i[2] ) > int( max_container_pid ):
                max_container_id = i[0]
                max_container_name = i[1]
                max_container_pid = i[2]

        ##KILL OLD PROCESSS AND START NEW MASTER PROCESS IN PYTHON


        zk.delete(slave_path + "/" + max_container_name, recursive=True)
        master_container_id_name_pid_string = str(max_container_id)+" "+str(max_container_name)+" "+str(max_container_pid)
        zk.set(master_path, master_container_id_name_pid_string.encode('utf-8'))
        print("NEW LEADER !! ", zk.get(master_path)[0].decode("utf-8"))


time.sleep(1)
current_master = zk.get(master_path)[0].decode("utf-8")
print("current master is:\t", current_master)
time.sleep(1)

zk.exists(master_path, watch = watch_master_node)
zk.set(master_path, b"")

time.sleep(1)


##########################

number_slaves_running = len(zk.get_children(slave_path))
number_slaves_needed = 0
number_slaves_to_spawn = number_slaves_needed - number_slaves_running

if number_slaves_to_spawn == 0:
    print("No Scale up or down.")
    
elif number_slaves_to_spawn > 0:
    for i in range(number_slaves_to_spawn):
        time.sleep(1)
        container_name = str("ws_"+str(slave_name_counter))
        client.containers.run("debian:stretch-slim", name=container_name, detach=True, tty=True)
        client.containers.get(container_name).exec_run("ls", detach =True)
        print("STARTED Slave container\t", container_name)
        slave_name_counter += 1

        container_id = client.containers.get(container_name).id
        container_name = client.containers.get(container_name).name
        stream = os.popen("sudo docker inspect --format '{{ .State.Pid }}' " +'"' + str(container_id) + '"' )
        #DOCKER IP ADDRESS sudo sudo docker inspect -f '{{.NetworkSettings.IPAddress }}' wm01
        container_pid = stream.read()
        container_pid = int(container_pid)

        zk.create(slave_path + "/" + str(container_name))
        slave_container_id_name_pid_string = str(container_id)+" "+str(container_name)+" "+str(container_pid)
        zk.set(slave_path + "/" + str(container_name), slave_container_id_name_pid_string.encode('utf-8'))

    print("Finished Scale Up")

else:
    for i in range( number_slaves_to_spawn * -1 ):
        time.sleep(1)
        slave_list = zk.get_children(slave_path)
        slave_container_id_name_pid=[]
        for slave in slave_list:
            data, stat = zk.get(slave_path + "/" + slave)
            data = str( data.decode("utf-8") ).split(" ")
            slave_container_id_name_pid.append(data)
        
        if( len(slave_container_id_name_pid) == 1):
            print("Scale Down Cancel !! No Slaves to pick from")
            break
        
        else:
            max_container_id = -1
            max_container_name = -1
            max_container_pid = -1

            for i in slave_container_id_name_pid:
                if int( i[2] ) > int( max_container_pid ):
                    max_container_id = i[0]
                    max_container_name = i[1]
                    max_container_pid = i[2]

            client.containers.get(max_container_name).stop()
            client.containers.get(max_container_name).remove()
            zk.delete(slave_path + "/" + max_container_name, recursive=True)
            print("Deleted container\t",max_container_name)


print(zk.get_children(slave_path))

"""
time.sleep(1)
try:
    current_master = zk.get(master_path)[0].decode("utf-8").split(" ")[1]
    print("current master is:\t", current_master)
    time.sleep(1)
    docker.stop(current_master)
    docker.remove(current_master)
    zk.exists(master_path, watch = watch_master_node)
    zk.set(master_path, b"")
except:
    pass

time.sleep(1)
try:
    current_master = zk.get(master_path)[0].decode("utf-8").split(" ")[1]
    print("current master is:\t", current_master)
    time.sleep(1)
    docker.stop(current_master)
    docker.remove(current_master)
    zk.exists(master_path, watch = watch_master_node)
    zk.set(master_path, b"")
except:
    pass

time.sleep(1)
try:
    current_master = zk.get(master_path)[0].decode("utf-8").split(" ")[1]
    print("current master is:\t", current_master)
    time.sleep(1)
    docker.stop(current_master)
    docker.remove(current_master)
    zk.exists(master_path, watch = watch_master_node)
    zk.set(master_path, b"")
except:
    pass

"""



#"""
running_containers = client.containers.list()
for i in running_containers:
    if str(i.name).startswith("w"):
        i.stop()
        i.remove()
print("Removed all master and slaves containers")
#"""

zk.stop()