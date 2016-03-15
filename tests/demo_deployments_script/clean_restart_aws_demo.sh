NEVERWINTERDP_DEPLOYMENTS_DIR=/home/neverwinterdp/neverwinterdp-deployments
ES_PUBLIC_DNS=ec2-52-32-12-37.us-west-2.compute.amazonaws.com

ssh -t centos@$ES_PUBLIC_DNS "sudo kill -9 $(ps aux | grep 'elasticsearch' | awk '{print $2}')"
ssh -t centos@$ES_PUBLIC_DNS "sudo rm -rf /var/lib/elasticsearch/*"
ssh -t centos@$ES_PUBLIC_DNS "sudo rm -rf /var/log/elasticsearch/*"



$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "odyssey_event_gen" --force-stop
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "kafka,zookeeper" --force-stop
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "gripper" --force-stop
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "storm_zookeeper" --force-stop
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "storm_nimbus" --force-stop
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "storm_supervisor" --force-stop
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "storm_code" --force-stop
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "kibana" --force-stop



$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "kafka,zookeeper" --clean
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "storm_zookeeper" --clean


ssh -t centos@$ES_PUBLIC_DNS "sudo systemctl start elasticsearch"

echo "Allow elasticsearch to start"
sleep 15

curl -XDELETE "http://$ES_PUBLIC_DNS:9200/_all/"
curl -XPUT "http://$ES_PUBLIC_DNS:9200/storm/"
curl -XPUT "http://$ES_PUBLIC_DNS:9200/storm/_mapping/docs" -d '{"docs": {"_timestamp": {"enabled": true},"properties": {"event": {"properties": {"actionType": {"type": "string", "index":"not_analyzed"},"ts" : { "type" : "date" }}}}}}'

$(npm config get prefix)/bin/elasticdump \
      --input=$NEVERWINTERDP_DEPLOYMENTS_DIR/ansible/roles/odyssey_kibana_charts/files/kibana.json \
      --output="http://$ES_PUBLIC_DNS:9200/.kibana" --type=data


$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "kafka,zookeeper" --start
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "gripper" --start
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "storm_zookeeper" --start
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "storm_nimbus" --start
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "storm_supervisor" --start
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "storm_code" --start
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "kibana" --start
$NEVERWINTERDP_DEPLOYMENTS_DIR/tools/serviceCommander/serviceCommander.py -e "odyssey_event_gen" --start