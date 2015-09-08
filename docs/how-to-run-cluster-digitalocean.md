## How to run performance tests with different profile in digitalocean using clustercommander


### Launching digitalocean machine with different configuration
1. ```git clone git@bitbucket.org:nventdata/neverwinterdp-deployments.git```
2. Go to the directory where you checkout the code
3. To configure how many machines and what size get launched in digital ocean (i.e. 8 gb vs 16 gb etc), You can modify file which is in the location<br/> 
```cd $NEVERWINTERDP_DEPLOYEMENTS_HOME/tools/cluster/digitalOceanConfigs```<br/>There are two files scribenginPerformance.yml and scribenginSmall.yml, you can edit any one of them.
4. ```cd $NEVERWINTERDP_DEPLOYEMENTS_HOME/tools/cluster/```
5. ```./clusterCommander.py digitalocean --launch --neverwinterdp-home $NEVERWINTERDP_HOME --create-containers /home/neverwinterdp/fix/neverwinterdp-deployments/tools/cluster/digitalOceanConfigs/scribenginSmall.yml --subdomain small --reboot```. <br/>Note: Make sure that you have specified the correct configuration file that you modified. It should be given under --create-containers option. <br/>Run ```./clusterCommander.py digitalocean``` --help to get more help for digitalocean options.
6. At this point it will launch digitalocean machines. It will take time, please be patience till all the machines get launched.

### Applying software profiles
1. ```cd $NEVERWINTERDP_DEPLOYEMENTS_HOME/tools/cluster/profile/```
2. Modify the profile as you want 
3. Run any tests under the location ```$NEVERWINTERDP_DEPLOYEMENTS_HOME/tests/scribengin/integration-tests/``` <br/>Example:```./tests/scribengin/integration-tests/Log_Sample_Chain.sh --stop --clean --build --deploy --start --profile-type=default  2>&1 | tee output.txt```
<br/>Note: Make sure the profile type that you have specified is the one that you modified.

