#!/bin/sh

#Update ansible inventory file
echo "Update ansible inventory file****************************"
./tools/awsHelper/awsHelper.py ansibleinventory --identifier odyssey,neverwinterdp

#Update hosts file on all instances
echo "Update hosts file on all instances***************************"
./tools/awsHelper/awsHelper.py updateremotehostfile -i odyssey,neverwinterdp -k /home/neverwinterdp/test.pem 


#Install, configure and start all services
echo "Install, configure and start all services************************"
./tools/serviceCommander/serviceCommander.py -e "kafka,zookeeper" --force-stop --clean --configure --start 
./tools/serviceCommander/serviceCommander.py -e "gripper" --install --configure --start 
./tools/serviceCommander/serviceCommander.py -e "load_balancer"  --install --configure --start 
./tools/serviceCommander/serviceCommander.py -e "odyssey_elasticsearch" --install --configure --start

./tools/serviceCommander/serviceCommander.py -e "storm_zookeeper" --install --configure --start
./tools/serviceCommander/serviceCommander.py -e "storm_nimbus" --install --configure --start
./tools/serviceCommander/serviceCommander.py -e "storm_supervisor" --install --configure --start
./tools/serviceCommander/serviceCommander.py -e "storm_code" --install --configure --start


