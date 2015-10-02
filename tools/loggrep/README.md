#Cluster LogGrep Tool#

Search through the logs on your cluster based on your ansible inventory file!

Constructs a find query to run on your cluster based on this:
```
find [find_folder] \( -iname "[find_iname]" \\) -exec grep [grep_options] '[grep_string]' {} \; -print
```

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
  yarn       Get YARN logs
  yarnapp    Get YARN App logs
  yarnvmapp  Get YARN VM App logs
  zookeeper  Get Zookeeper logs



####
Usage: loggrep.py cluster [OPTIONS]

  Get Cluster logs

Options:
  -g, --grep-options TEXT  Options for grep
  -s, --grep-string TEXT   What to grep for
  --help                   Show this message and exit.


#####
Usage: loggrep.py kafka [OPTIONS]

  Get Kafka logs

Options:
  -f, --find-folder TEXT   Folder to find logs
  -n, --find-iname TEXT    Name to look for - (find's -iname option)
  -g, --grep-options TEXT  Options for grep
  -s, --grep-string TEXT   What to grep for
  --help                   Show this message and exit.

```


##Examples##
```
#Search kafka logs
./loggrep.py -i /tmp/scribengininventoryDO kafka

#Search kafka and zookeeper logs
./loggrep.py -i /tmp/scribengininventoryDO kafka zookeeper

#Search the whole cluster's logs (kafka, zk, and hadoop)
./loggrep.py -i /tmp/scribengininventoryDO cluster

#Search Kafka logs for "info"
./loggrep.py -i /tmp/scribengininventoryDO kafka -s info

#Search Kafka logs, use custom grep options
./loggrep.py -i /tmp/scribengininventoryDO kafka -g "-i -c"


#Change up the search.  The following command will run on all your kafka machines:
#find /opt/new_kafka_folder \( -iname "*.log" \) -exec grep -i -c 'searchString' {} \; -print
./loggrep.py -i /tmp/scribengininventoryDO kafka --find-folder /opt/new_kafka_folder --find-iname "*.log" --grep-option "-i -c" --grep-string "searchString"

#Search all cluster logs with custom search string and grep optoins
./loggrep.py -i /tmp/scribengininventoryDO cluster -g "-i -c" -s searchString

```

