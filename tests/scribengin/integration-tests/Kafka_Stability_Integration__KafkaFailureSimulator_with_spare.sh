#V2/docker/scribengin/integration-tests/Kafka_Stability_Integration__KafkaFailureSimulator.sh
./V2/docker/scribengin/docker.sh cluster --clean-containers --run-containers --kafka-server=5 --deploy-scribengin
ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster && 				\
									./clusterCommander.py zookeeper --clean --start kafka --clean --start"

#make folder for test results
mkdir testresults

#Give everything time to come up
sleep 5


#Run failure simulator in the background
ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster && mkdir -p /opt/scribengin/scribengin/tools/kafka/junit-reports"
ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster &&                                     \
                                  python clusterCommander.py --debug kafkafailure                                    \
                                  --wait-before-start 30 --failure-interval 30 --kill-method restart                 \
                                  --servers-to-fail-simultaneously 2                                                 \
                                  --use-spare 2                           						\
                                  --restart-method flipflop                                                      	 \
                                  --junit-report /opt/scribengin/scribengin/tools/kafka/junit-reports/kafkaFailureReport.xml" &
FAIL_SIM_PID=$!

ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster && \
                                    python clusterCommander.py  monitor --update-interval 10 " &

MONITOR_PID=$!


#Run kafkaStabilityCheckTool
ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/scribengin/scribengin/tools/kafka/ &&     \
                              ./kafka.sh test stability --zk-connect zookeeper-1:2181 --topic stabilitytest      \
                              --replication 3 --send-period 0 --send-writer-type ack --send-max-duration 1800000 \
                              --send-max-per-partition 2000000 --producer:message.send.max.retries=5            \
                              --producer:retry.backoff.ms=100 --producer:queue.buffering.max.ms=1000             \
                              --producer:queue.buffering.max.messages=15000                                      \
                              --producer:topic.metadata.refresh.interval.ms=-1 --producer:batch.num.messages=100 \
                              --producer:acks=all --producer:compression.type=gzip --consume-max 10000000       \
                              --consume-max-duration 60000000                                                     \
                              --junit-report junit-reports/KafkaMessageCheckTool.xml"


#Get results
scp -o stricthostkeychecking=no neverwinterdp@hadoop-master:/opt/scribengin/scribengin/tools/kafka/junit-reports/*.xml ./testresults/

kill -9 $FAIL_SIM_PID $MONITOR_PID

#Clean up
./V2/docker/scribengin/docker.sh cluster --clean-containers
