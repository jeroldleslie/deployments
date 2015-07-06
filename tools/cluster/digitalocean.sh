#!/bin/bash

bin=`dirname "$0"`
bin=`cd "$bin"; pwd`

PROJECT_DIR=`cd $bin/../..; pwd; cd $bin`

$PROJECT_DIR/tools/cluster/clusterCommander.py digitalocean \
  --launch --neverwinterdp-home $NEVERWINTERDP_HOME   \
  --create-containers   $PROJECT_DIR/tools/cluster/digitalOceanConfigs/scribenginPerformance.yml  cluster --start  \
  --kafka-server-config $PROJECT_DIR/configs/bootstrap/post-install/kafka/config/server.properties     \
  --zookeeper-server-config $PROJECT_DIR//configs/bootstrap/post-install/zookeeper/conf/zoo.cfg

