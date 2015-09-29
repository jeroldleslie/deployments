#Service Commander#
Use Ansible to manage services in your cluster!

##Usage##
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
  -r, --restart              restart services
  -s, --start                start services
  -t, --stop                 stop services
  -f, --force-stop           kill services
  -f, --clean                clean services
  -n, --install              install services
  -c, --configure            configure services
  --ansible-root-dir TEXT    Root directory for Ansible
  -m, --max-retries INTEGER  Max retries for running the playbook
  --help                     Show this message and exit.
  ```

##Setup##
```
sudo pip install click
```

##Directory Structure Setup##
- You must have a directory structure to support Service Commander
- Each service must have its own playbook
- Each service you attempt to use must correspond to a role in your [ansible-root-dir]
- Example:
    
  ```
      .
      └── tools/
        └── ansible/
        |    ├── kafka.yml
        |    ├── zookeeper.yml
        |    └── roles/
        |      └──  kafka/
        |      └──  zookeeper/
        |      └──  common/
        └── serviceCommander/
            └── serviceCommander.py
  ```


##Playbook Setup##


##Examples##
Using the above structure as an example...
```
#Install, configure, and start kafka and zookeeper
./serviceCommander.py --services kafka,zookeeper --install --configure --start 

#Start zookeeper
./serviceCommander.py --services zookeeper --start

#Start kafka and point to a non-default ansible-root-dir
./serviceCommander.py --services kafka --start --ansible-root-dir /etc/ansible/
```

