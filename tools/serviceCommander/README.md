#serviceCommander#
Use Ansible to manage services in your cluster!

serviceCommander is a thin front-end for ansible playbooks. serivceCommander holds some options to automatically pick a specific service or group of service to perform pre-defined operations like install,configure,start,stop,force-stop,clean.


###Usage
```
Usage: serviceCommander.py [OPTIONS]

  Use Ansible to manage services in your cluster!

Options:
  --debug / --no-debug       Turn debugging on
  --logfile TEXT             Log file to write to
  -e, --services TEXT        Services to impact input as a comma separated
                             list
  -l, --subset TEXT          Further limit selected hosts with an additional
                             pattern
  -i, --inventory-file TEXT  Ansible inventory file to use
  -u, --cluster              Alternative to --services option, runs for entire
                             cluster
  -s, --start                start services
  -t, --stop                 stop services
  -f, --force-stop           kill services
  -a, --clean                clean services
  -n, --install              install services
  -c, --configure            configure services
  -p, --profile-type TEXT    profile type for service configuration
  --ansible-root-dir TEXT    Root directory for Ansible
  -m, --max-retries INTEGER  Max retries for running the playbook
  -v, --extra-vars TEXT      Extra variable for the playbook
  --help                     Show this message and exit.

```
#####Note: 
Service name should be eqaul to the playbook name. ex: If ```--services "serviceX"``` then ansible playbook should be ```serviceX.yml```

###Examples
Using the below structure as an example...

```

#Start all cluster services
./serviceCommander.py --cluster --start

#Install, configure, force-stop, clean, restart cluster
./serviceCommander.py --cluster --install --configure --force-stop --clean --start

#Start all cluster services and also two extra services called serviceX and serviceY
./serviceCommander.py --cluster --services serviceX,serviceY  --start

#Install, configure, and start kafka and zookeeper
./serviceCommander.py --services kafka,zookeeper --install --configure --start 

#Start zookeeper
./serviceCommander.py --services zookeeper --start

#Start kafka and point to a non-default ansible-root-dir
./serviceCommander.py --services kafka --start --ansible-root-dir /etc/ansible/
```








