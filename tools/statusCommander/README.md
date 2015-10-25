#statusCommander

Get your cluster's status based on your ansible inventory file!


###Usage

```
Usage: statusCommander.py [OPTIONS]

  Get your cluster's status based on your ansible inventory file!

Options:
  --debug / --no-debug         Turn debugging on
  --logfile TEXT               Log file to write to
  -m, --timeout INTEGER        SSH timeout time (seconds)
  -i, --inventory-file TEXT    Ansible inventory file to use
  -n, --monitor                Run continuously
  -s, --monitor-sleep INTEGER  How long to sleep between checks while
                               monitoring
  --help                       Show this message and exit.

```

###Example

```
#Normal usage
user@machine:statusCommander $ ./statusCommander.py -i inventoryFile

#To change the number of threads to run at a time
user@machine:statusCommander $ ./statusCommander.py -i inventoryFile --threads 5

#To change the amount of time on an ssh connection before timing out
user@machine:statusCommander $ ./statusCommander.py -i inventoryFile --timeout 45
```

###Example Output
```
Role           Hostname         ProcessIdentifier                               ProcessID    Status
-------------  ---------------  ----------------------------------------------  -----------  -----------
monitoring     monitoring-1
                                kibana                                          ----         --- Stopped
hadoop_master  hadoop-master
                                SecondaryNameNode                               25462        Running
                                ResourceManager                                 25532        Running
                                NameNode                                        25371        Running
zookeeper      zookeeper-1
                                QuorumPeerMain                                  11049        Running
               kafka-1
                                QuorumPeerMain                                  ----         --- Stopped
kafka          kafka-2
                                Kafka                                           12162        Running
               kafka-3
                                Kafka                                           11649        Running
               kafka-1
                                Kafka                                           11566        Running
hadoop_worker  hadoop-worker-3
                                DataNode                                        24898        Running
                                NodeManager                                     25001        Running
                                vm-master-1                                     27600        Running
                                log-persister-dataflow-warn-master-0000000003   28766        Running
                                log-splitter-dataflow-worker-0000000002         28100        Running
                                log-splitter-dataflow-worker-0000000001         27970        Running
                                log-persister-dataflow-info-worker-0000000003   28591        Running
                                log-persister-dataflow-info-worker-0000000004   28617        Running
               hadoop-worker-1
                                DataNode                                        21486        Running
                                NodeManager                                     21589        Running
                                log-persister-dataflow-info-master-0000000002   24186        Running
                                log-persister-dataflow-warn-worker-0000000005   24429        Running
                                log-persister-dataflow-warn-worker-0000000006   24558        Running
               hadoop-worker-2
                                DataNode                                        19063        Running
                                NodeManager                                     19166        Running
                                vm-scribengin-master-1                          21576        Running
                                log-persister-dataflow-error-master-0000000004  22485        Running
                                log-splitter-dataflow-master-0000000001         22222        Running
                                log-persister-dataflow-error-worker-0000000008  22847        Running
                                log-persister-dataflow-error-worker-0000000007  22706        Running
                                vm-log-generator-1                              22028        Running
elasticsearch  elasticsearch-1
                                Main                                            15376        Running
```