#SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#This Script will set root directory and Neverwinter_home
source $SCRIPT_DIR/setupEnvironment.sh $@



#Run failure simulator in the background
ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster && mkdir -p /opt/neverwinterdp/scribengin/tools/kafka/junit-reports"
ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster &&                                     \
                                  python clusterCommander.py --debug kafkafailure                                    \
                                  --wait-before-start 30 --failure-interval 30 --kill-method shutdown                 \
                                  --servers-to-fail-simultaneously 1                                                 \
                                  --junit-report /opt/neverwinterdp/scribengin/tools/kafka/junit-reports/kafkaFailureReport.xml" &
FAIL_SIM_PID=$!

ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster && \
                                    python clusterCommander.py  monitor --update-interval 10 " &
MONITOR_PID=$!


#Run kafkaStabilityCheckTool
ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/neverwinterdp/scribengin/tools/kafka/ &&     \
                              ./kafka.sh test stability --zk-connect zookeeper-1:2181 --topic stabilitytest      \
                              --replication 3 --send-period 0 --send-writer-type ack --send-max-duration 1800000 \
                              --send-max-per-partition 20000000 --producer:message.send.max.retries=5            \
                              --producer:retry.backoff.ms=100 --producer:queue.buffering.max.ms=1000             \
                              --producer:queue.buffering.max.messages=15000                                      \
                              --producer:topic.metadata.refresh.interval.ms=-1 --producer:batch.num.messages=100 \
                              --producer:acks=all --producer:compression.type=gzip --consume-max 100000000       \
                              --consume-max-duration 6000000                                                     \
                              --junit-report junit-reports/KafkaMessageCheckTool.xml"


#Get results
scp -o stricthostkeychecking=no neverwinterdp@hadoop-master:/opt/neverwinterdp/scribengin/tools/kafka/junit-reports/*.xml $TEST_RESULTS_LOCATION

kill -9 $FAIL_SIM_PID $MONITOR_PID
