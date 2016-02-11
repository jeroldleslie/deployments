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
$serviceCommander -e "gripper" --install --configure --start 
$serviceCommander -e "load_balancer"  --install --configure --start 
$serviceCommander -e "odyssey_elasticsearch" --install --configure --start

$serviceCommander -e "storm_zookeeper" --install --configure --start
$serviceCommander -e "storm_nimbus" --install --configure --start
$serviceCommander -e "storm_supervisor" --install --configure --start
$serviceCommander -e "storm_code" --install --configure --start
