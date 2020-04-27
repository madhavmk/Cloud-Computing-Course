import docker
import os

client = docker.from_env()


new_worker_name_list=["w1","w2","w3"]
for new_worker_name in new_worker_name_list:
    client.containers.run("worker:v1", name=new_worker_name, detach=True)
    client.containers.get(new_worker_name).exec_run("python3 Cloud-Computing-Course/Database/Database/rpc_server_database.py 1", detach =True)


running_containers = client.containers.list() # running_containers = client.containers.list(all=True)
running_containers_id_name_pid=[]
for i in running_containers:
    container_id = i.id
    container_name = i.name
    stream = os.popen("sudo docker inspect --format '{{ .State.Pid }}' " +'"' + str(container_id) + '"' )
    #DOCKER IP ADDRESS sudo sudo docker inspect -f '{{.NetworkSettings.IPAddress }}' wm01
    container_pid = stream.read()
    container_pid = int(container_pid)
    running_containers_id_name_pid.append( [str(container_id),str(container_name),str(container_pid)] )

print(running_containers_id_name_pid)

master_file_handle = open("master.txt","w") 
slave_file_handle = open("slave.txt","w") 

if(len(running_containers_id_name_pid)>=1):
    master_file_handle.write(" ".join(running_containers_id_name_pid[0]))

if(len(running_containers_id_name_pid)>=2):
    for i in range(1,len(running_containers_id_name_pid)):
        slave_file_handle.write(" ".join(running_containers_id_name_pid[i]))


master_file_handle.close()
slave_file_handle.close()