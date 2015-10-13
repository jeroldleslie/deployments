#!/bin/bash

#SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#This Script will set root directory and Neverwinter_home
source $SCRIPT_DIR/setupEnvironment.sh $@



#Run failure simulator in the background
ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "mkdir -p /opt/neverwinterdp/junit-reports"
ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster &&                                     \
								  sleep 300 &&                                                                      \
                                  python clusterCommander.py --debug kafkafailure                                   \
                                  --wait-before-start 120 --failure-interval 120 --kill-method shutdown               \
                                  --servers-to-fail-simultaneously 1                                                \
                                  --junit-report /opt/neverwinterdp/junit-reports/kafkaFailureReport.xml" &
FAIL_SIM_PID=$!

ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster && \
                                    python clusterCommander.py  monitor --update-interval 30 " &
MONITOR_PID=$!


#Run stability test
ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/neverwinterdp/ &&  ./dataflow/log-sample/bin/run-dataflow-chain.sh   \
														--num-of-message=1000000  --generator-max-wait-time=10000 --generator-send-period=1 \
														--monitor-max-runtime=604800000 --max-run-time=604800000                           \
														--dedicated-executor=false --num-of-worker=2 --num-of-executor-per-worker=2         \
														--num-of-stream=8 --message-size=512                                                \
														--junit-report junit-reports/ScribenginKafkaFailureStability.xml"


#Get results
scp -o stricthostkeychecking=no neverwinterdp@hadoop-master:/opt/neverwinterdp/junit-reports/*.xml $TEST_RESULTS_LOCATION

kill -9 $FAIL_SIM_PID $MONITOR_PID



clusterCommander.py --debug kafkafailure --wait-before-start 90 --failure-interval 90 --kill-method shutdown --servers-to-fail-simultaneously 1 