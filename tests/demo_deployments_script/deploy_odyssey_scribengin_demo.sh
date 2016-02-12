#!/bin/sh

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
ROOT=$SCRIPT_DIR/../..

serviceCommander="$ROOT/tools/serviceCommander/serviceCommander.py"
awsHelper="$ROOT/tools/awsHelper/awsHelper.py"

#Update ansible inventory file
echo "Update ansible inventory file****************************"
$awsHelper ansibleinventory --identifier odyssey,neverwinterdp

#Update hosts file on all instances
echo "Update hosts file on all instances***************************"
$awsHelper updateremotehostfile -i odyssey,neverwinterdp -k /home/neverwinterdp/test.pem 

#Install, configure and start all services
echo "Install, configure and start all services************************"
$serviceCommander -e "kafka,zookeeper" --force-stop --clean --configure --start 
$serviceCommander -e "gripper" --force-stop --install --configure --start 
$serviceCommander -e "load_balancer"  --force-stop --install --configure --start 
$serviceCommander -e "odyssey_elasticsearch" --force-stop --install --configure --start

$serviceCommander -e "storm_zookeeper" --force-stop --install --configure --start --clean
$serviceCommander -e "storm_nimbus" --force-stop --install --configure --start
$serviceCommander -e "storm_supervisor" --force-stop --install --configure --start
$serviceCommander -e "storm_code" --force-stop --install --configure --start
