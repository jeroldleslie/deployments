#Status Commander#
Get your cluster's status based on your ansible inventory file!

##Usage##
```
Usage: statusCommander.py [OPTIONS]

  Get your cluster's status based on your ansible inventory file!

Options:
  --debug / --no-debug       Turn debugging on
  --logfile TEXT             Log file to write to
  -t, --threads INTEGER      Number of threads to run simultaneously
  -i, --inventory-file TEXT  Ansible inventory file to use
  --help                     Show this message and exit.
```

##Example usage##
```
user@machine:statusCommander $ ./statusCommander.py -i /tmp/scribengininventoryDO
Role           Hostname         ProcessIdentifier                               ProcessID    Status
-------------  ---------------  ----------------------------------------------  -----------  --------
monitoring     monitoring-1
                                                                                             Stopped
hadoop_master  hadoop-master
                                SecondaryNameNode                               21626        Running
                                ResourceManager                                 21696        Running
                                NameNode                                        21535        Running
zookeeper      zookeeper-1
                                QuorumPeerMain                                  9893         Running
kafka          kafka-2
                                Kafka                                           10620        Running
               kafka-3
                                Kafka                                           10526        Running
               kafka-1
                                Kafka                                           10446        Running
hadoop_worker  hadoop-worker-3
                                DataNode                                        8246         Running
                                NodeManager                                     8349         Running
                                vm-scribengin-master-1                          10981        Running
                                log-persister-dataflow-info-master-0000000002   11858        Running
                                log-persister-dataflow-error-master-0000000004  12408        Running
                                log-splitter-dataflow-worker-0000000001         11564        Running
                                log-splitter-dataflow-worker-0000000002         11694        Running
               hadoop-worker-1
                                DataNode                                        6572         Running
                                NodeManager                                     6675         Running
                                vm-master-1                                     9081         Running
                                log-persister-dataflow-error-worker-0000000008  10214        Running
                                log-persister-dataflow-warn-worker-0000000005   9593         Running
                                log-persister-dataflow-warn-worker-0000000006   9724         Running
                                log-persister-dataflow-error-worker-0000000007  10086        Running
               hadoop-worker-2
                                DataNode                                        6814         Running
                                NodeManager                                     6917         Running
                                log-persister-dataflow-warn-master-0000000003   10393        Running
                                log-splitter-dataflow-master-0000000001         9870         Running
                                log-persister-dataflow-info-worker-0000000003   10120        Running
                                log-persister-dataflow-info-worker-0000000004   10252        Running
elasticsearch  elasticsearch-1
                                Main                                            11281        Running
````