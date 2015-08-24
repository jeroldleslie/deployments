* Make sure you have recently run ```./docker.sh cluster --clean-image --build-image```
* Then run ```./testDocker.sh```
* Flink will be deployed on hadoop-master under /opt/flink
* Storm will use zookeeper on storm-zookeeper, and be deployed on storm-nimbus, storm-supervisor-*
* You can access the Storm UI via http://storm-nimbus:8080/index.html
* You're on your own for Flink, but it should run in YARN (which should be running as expected)