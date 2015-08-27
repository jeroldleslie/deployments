* Make sure you have recently run ```./docker.sh cluster --clean-image --build-image```
* Then run ```cd Neverwinterdp-Deployments/docker/flinkStormTest/ && ./testDocker.sh```
* Flink will be deployed on hadoop-master under /opt/flink
* Storm will use zookeeper on storm-zookeeper, and be deployed on storm-nimbus, storm-supervisor-*
* You can access the Storm UI via http://storm-nimbus:8080/index.html
* You're on your own for Flink, but it should run in YARN (which should be running as expected)

#To Run

export HADOOP_HOME=/opt/hadoop && ./bin/yarn-session.sh -n 15 -tm 8192
./bin/yarn-session.sh -n 5 -tm 4096

wget -O hamlet.txt http://www.gutenberg.org/cache/epub/1787/pg1787.txt
/opt/hadoop/bin/hdfs dfs -mkdir /tmp
/opt/hadoop/bin/hdfs dfs -copyFromLocal hamlet.txt /tmp
/opt/hadoop/bin/hdfs dfs -rm /tmp/wordcount-result.txt
./bin/flink run ./examples/flink-java-examples-0.9.0-WordCount.jar hdfs://hadoop-master:9000/tmp/hamlet.txt hdfs://hadoop-master:9000/tmp/wordcount-result.txt
