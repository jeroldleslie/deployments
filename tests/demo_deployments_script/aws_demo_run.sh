#!/bin/sh
counter=0
gripper_host=$1
echo $gripper_host
key_secret="OvQVG3oQGsC07YFeaJLrXViNNBmj28f6X5Yk0ORKGFt1oMBEiHDQlGQoCxhyjTv9ub4BwI6FIe9Y"
while true; do
   counter=`expr $counter + 1`
   ts=$(date +%s)
   echo 'ts' $ts
   date_ts=$(date)
   echo 'date_ts' $date_ts
   hmac="$(printf "$ts" | openssl sha1 -binary -hmac "$key_secret" | base64)"
   curl  -X POST $gripper_host/message/test-topic1/sync -d '{"event": {"id":'$counter',"type": "demonow-did-something","ts": '$ts', "hmac": "'$hmac'" }} '
   echo 'Sending message : {"event": {"id":'$counter',"type": "demonow-did-something","ts": '$ts',"date":"'$date_ts'", "hmac": "'$hmac'" }} '
#   sleep 1
done

# Run this file multiple times parallely
#for((i=1;i<100;i++)); do nohup ./aws_demo_run.sh ec2-52-32-241-54.us-west-2.compute.amazonaws.com > aws_demo_run.log 2>&1& & done

# Using GNU Parallel in MAC OS or any other machine
#seq 1 10000 | parallel -j20 ./aws_demo_run.sh
# Use this to kill all the commands
#kill $(ps aux | grep 'aws_demo_run.sh' | awk '{print $2}')
