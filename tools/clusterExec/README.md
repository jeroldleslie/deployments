#Cluster Execute Tool#

Execute arbitrary commands based on your ansible inventory file!

Tell this tool which group to execute on, and it will execute the command passed in on all machines in that group

##Installation##

```
user@machine: $ sudo pip install ansible click paramiko
```


##Usage##

```
Usage: clusterExec.py [OPTIONS]

  Get your cluster's status based on your ansible inventory file!

Options:
  --debug / --no-debug       Turn debugging on
  --logfile TEXT             Log file to write to
  -g, --group TEXT           Ansible group to execute on  [required]
  -c, --command TEXT         Command to execute  [required]
  -i, --inventory-file TEXT  Path to inventory file to use  [required]
  -t, --timeout INTEGER      SSH timeout time (seconds)
  --help                     Show this message and exit.

```


##Examples##
```
#See below for sample inventory file

#Execute command on all hosts in the hadoop_worker group.  Assumes inventory file is at ./inventory
./clusterExec.py -g hadoop_worker -c "ls -la"

#Execute command on all hosts in the zookeeper group
./clusterExec.py -g zookeeper -c "ls -la"

#Execute command on all hosts in the kafka group, set the SSH timeout to 10 seconds, specify inventory file
./clusterExec.py -i /tmp/scribengininventoryDO -g kafka -c "ls -la" -t 10

#Special case: Execute command on all hosts in the inventory file
./clusterExec.py -g cluster -c "ls -la"

#Special case: Execute command on hosts in hadoop_worker and hadoop_master group
./clusterExec.py -g hadoop -c "ls -la"


```

Based on an inventory file that looks like the following:
```
[monitoring]
monitoring-1 ansible_ssh_user=neverwinterdp ansible_ssh_private_key_file=~/.ssh/id_rsa

[kafka]
kafka-2 ansible_ssh_user=neverwinterdp ansible_ssh_private_key_file=~/.ssh/id_rsa
kafka-1 ansible_ssh_user=neverwinterdp ansible_ssh_private_key_file=~/.ssh/id_rsa
kafka-3 ansible_ssh_user=neverwinterdp ansible_ssh_private_key_file=~/.ssh/id_rsa

[hadoop_master]
hadoop-master ansible_ssh_user=neverwinterdp ansible_ssh_private_key_file=~/.ssh/id_rsa

[hadoop_worker]
hadoop-worker-2 ansible_ssh_user=neverwinterdp ansible_ssh_private_key_file=~/.ssh/id_rsa
hadoop-worker-1 ansible_ssh_user=neverwinterdp ansible_ssh_private_key_file=~/.ssh/id_rsa
hadoop-worker-3 ansible_ssh_user=neverwinterdp ansible_ssh_private_key_file=~/.ssh/id_rsa

[zookeeper]
zookeeper-1 ansible_ssh_user=neverwinterdp ansible_ssh_private_key_file=~/.ssh/id_rsa

[elasticsearch]
elasticsearch-1 ansible_ssh_user=neverwinterdp ansible_ssh_private_key_file=~/.ssh/id_rsa
```

