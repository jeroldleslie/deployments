#Cluster LogGrep Tool#

Search through your cluster's log based on your ansible inventory file!


##Installation##

```
user@machine: $ sudo pip install ansible click paramiko
```


##Usage##

```
Usage: loggrep.py [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

  Parse your cluster's logs!

Options:
  --debug / --no-debug       Turn debugging on
  --logfile TEXT             Log file to write to
  -t, --threads INTEGER      Number of threads to run simultaneously
  -m, --timeout INTEGER      SSH timeout time (seconds)
  -i, --inventory-file TEXT  Ansible inventory file to use
  --help                     Show this message and exit.

Commands:
  cluster    Get Cluster logs
  hadoop     Get Hadoop logs
  kafka      Get Kafka logs
  zookeeper  Get Zookeeper logs
```


##Examples##
```
#Search kafka logs
./loggrep.py -i /tmp/scribenginInventoryDO kafka

#Search kafka and zookeeper logs
./loggrep.py -i /tmp/scribenginInventoryDO kafka zookeeper

#Search the whole cluster's logs (kafka, zk, and hadoop)
./loggrep.py -i /tmp/scribenginInventoryDO cluster

#Run a custom command on your cluster
./loggrep.py -i /tmp/scribengininventoryDO cluster -c "cat /etc/hosts"

```

